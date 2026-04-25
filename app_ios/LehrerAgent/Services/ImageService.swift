// ImageService.swift
// Kamera-Zugriff, Bildoptimierung und Perspektivkorrektur für Schülerarbeiten.
//
// Ablauf:
//   1. Foto aufnehmen (Kamera oder Galerie)
//   2. Bild auf max. 1600px skalieren
//   3. Als JPEG mit Qualität 85% komprimieren → typisch ~200–400 KB
//   4. Optimiertes JPEG-Data zurückgeben für ConnectionService

import UIKit
import CoreImage
import PhotosUI
import SwiftUI

// MARK: - Optimiertes Bild

struct OptimizedImage {
    let jpegData: Data
    let widthPx: Int
    let heightPx: Int
    let originalSizeKB: Int
    let optimizedSizeKB: Int

    var compressionRatio: Double {
        guard originalSizeKB > 0 else { return 1 }
        return Double(optimizedSizeKB) / Double(originalSizeKB)
    }
}

// MARK: - ImageService

class ImageService {

    // Maximale Breite/Höhe nach Skalierung (reicht für gute OCR-Qualität)
    static let maxDimension: CGFloat = 1600

    // JPEG-Komprimierungsqualität (0.85 = sehr gute Qualität, ~5–10x kleiner als Original)
    static let jpegQuality: CGFloat = 0.85

    // MARK: - Bild optimieren

    /// Skaliert und komprimiert ein UIImage für die Übertragung.
    /// Schülerarbeiten sind oft 12 MP+, das wäre viel zu groß für die Übertragung.
    static func optimize(_ image: UIImage) -> OptimizedImage? {
        // Originalgröße schätzen
        let originalData = image.jpegData(compressionQuality: 1.0)
        let originalSizeKB = (originalData?.count ?? 0) / 1024

        // Bild skalieren
        let scaled = scale(image, maxDimension: maxDimension)

        // JPEG komprimieren
        guard let jpegData = scaled.jpegData(compressionQuality: jpegQuality) else {
            return nil
        }

        let width = Int(scaled.size.width)
        let height = Int(scaled.size.height)
        let optimizedSizeKB = jpegData.count / 1024

        return OptimizedImage(
            jpegData: jpegData,
            widthPx: width,
            heightPx: height,
            originalSizeKB: originalSizeKB,
            optimizedSizeKB: optimizedSizeKB
        )
    }

    // MARK: - Skalierung

    private static func scale(_ image: UIImage, maxDimension: CGFloat) -> UIImage {
        let size = image.size
        let maxSide = max(size.width, size.height)

        // Kleiner als maxDimension → nichts zu tun
        if maxSide <= maxDimension {
            return image
        }

        let scale = maxDimension / maxSide
        let newSize = CGSize(width: size.width * scale, height: size.height * scale)

        let renderer = UIGraphicsImageRenderer(size: newSize)
        return renderer.image { _ in
            image.draw(in: CGRect(origin: .zero, size: newSize))
        }
    }

    // MARK: - Perspektivkorrektur (automatisch)

    /// Versucht, eine schräg fotografierte Schülerarbeit automatisch zu begradigen.
    /// Funktioniert gut wenn der Kontrast zwischen Papier und Untergrund hoch ist.
    /// Falls kein Rechteck erkannt wird: Originalbild zurückgeben.
    static func perspectiveCorrect(_ image: UIImage) -> UIImage {
        guard let ciImage = CIImage(image: image) else { return image }

        let detector = CIDetector(
            ofType: CIDetectorTypeRectangle,
            context: nil,
            options: [CIDetectorAccuracy: CIDetectorAccuracyHigh]
        )

        guard let features = detector?.features(in: ciImage),
              let rect = features.first as? CIRectangleFeature
        else {
            return image // Kein Rechteck erkannt → unverändert
        }

        let corrected = ciImage.applyingFilter("CIPerspectiveCorrection", parameters: [
            "inputTopLeft":     CIVector(cgPoint: rect.topLeft),
            "inputTopRight":    CIVector(cgPoint: rect.topRight),
            "inputBottomLeft":  CIVector(cgPoint: rect.bottomLeft),
            "inputBottomRight": CIVector(cgPoint: rect.bottomRight)
        ])

        let context = CIContext()
        guard let cgImage = context.createCGImage(corrected, from: corrected.extent) else {
            return image
        }

        return UIImage(cgImage: cgImage)
    }
}

// MARK: - Kamera-Picker (SwiftUI)

/// UIImagePickerController als SwiftUI View.
/// Wird in CaptureView verwendet.
struct CameraPicker: UIViewControllerRepresentable {

    @Binding var capturedImage: UIImage?
    @Environment(\.dismiss) var dismiss

    var sourceType: UIImagePickerController.SourceType = .camera

    func makeUIViewController(context: Context) -> UIImagePickerController {
        let picker = UIImagePickerController()
        picker.sourceType = sourceType
        picker.delegate = context.coordinator
        picker.allowsEditing = false

        // Beste Qualität für OCR
        if sourceType == .camera {
            picker.cameraCaptureMode = .photo
            picker.cameraDevice = .rear
        }

        return picker
    }

    func updateUIViewController(_ uiViewController: UIImagePickerController, context: Context) {}

    func makeCoordinator() -> Coordinator {
        Coordinator(self)
    }

    class Coordinator: NSObject, UIImagePickerControllerDelegate, UINavigationControllerDelegate {
        let parent: CameraPicker

        init(_ parent: CameraPicker) {
            self.parent = parent
        }

        func imagePickerController(
            _ picker: UIImagePickerController,
            didFinishPickingMediaWithInfo info: [UIImagePickerController.InfoKey: Any]
        ) {
            if let image = info[.originalImage] as? UIImage {
                parent.capturedImage = image
            }
            parent.dismiss()
        }

        func imagePickerControllerDidCancel(_ picker: UIImagePickerController) {
            parent.dismiss()
        }
    }
}

// MARK: - Galerie-Picker (SwiftUI, iOS 16+)

struct GalleryPicker: UIViewControllerRepresentable {

    @Binding var capturedImage: UIImage?
    @Environment(\.dismiss) var dismiss

    func makeUIViewController(context: Context) -> PHPickerViewController {
        var config = PHPickerConfiguration()
        config.selectionLimit = 1
        config.filter = .images

        let picker = PHPickerViewController(configuration: config)
        picker.delegate = context.coordinator
        return picker
    }

    func updateUIViewController(_ uiViewController: PHPickerViewController, context: Context) {}

    func makeCoordinator() -> Coordinator {
        Coordinator(self)
    }

    class Coordinator: NSObject, PHPickerViewControllerDelegate {
        let parent: GalleryPicker

        init(_ parent: GalleryPicker) {
            self.parent = parent
        }

        func picker(_ picker: PHPickerViewController, didFinishPicking results: [PHPickerResult]) {
            parent.dismiss()

            guard let provider = results.first?.itemProvider,
                  provider.canLoadObject(ofClass: UIImage.self)
            else { return }

            provider.loadObject(ofClass: UIImage.self) { image, _ in
                DispatchQueue.main.async {
                    self.parent.capturedImage = image as? UIImage
                }
            }
        }
    }
}
