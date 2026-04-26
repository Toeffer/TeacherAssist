/// Quick Actions Widget für LehrerAgent
/// Schnellzugriff-Buttons für häufige Aktionen (besonders auf Mobile)
library quick_actions;

import 'package:flutter/material.dart';

/// Quick Action Item
class QuickAction {
  /// Titel der Aktion
  final String title;

  /// Beschreibung (optional)
  final String? description;

  /// Icon
  final IconData icon;

  /// Aktionstyp (für Routing/Handler)
  final String actionType;

  /// Farbe (optional)
  final Color? color;

  /// Ist aktiviert?
  final bool enabled;

  /// Callback bei Tap
  final VoidCallback onTap;

  /// Konstruktor
  const QuickAction({
    required this.title,
    this.description,
    required this.icon,
    required this.actionType,
    this.color,
    this.enabled = true,
    required this.onTap,
  });
}

/// Quick Actions Widget
class QuickActions extends StatelessWidget {
  /// Aktionen
  final List<QuickAction> actions;

  /// Layout-Orientierung
  final Axis direction;

  /// Soll Scrollen erlaubt sein?
  final bool scrollable;

  /// Maximale Breite pro Item (nur bei horizontaler Richtung)
  final double? maxItemWidth;

  /// Konstruktor
  const QuickActions({
    Key? key,
    required this.actions,
    this.direction = Axis.horizontal,
    this.scrollable = true,
    this.maxItemWidth,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;
    final isHorizontal = direction == Axis.horizontal;

    final content = ListView.builder(
      scrollDirection: direction,
      physics: scrollable
          ? const AlwaysScrollableScrollPhysics()
          : const NeverScrollableScrollPhysics(),
      shrinkWrap: true,
      itemCount: actions.length,
      itemBuilder: (context, index) {
        final action = actions[index];
        return _buildActionItem(context, action, isHorizontal, isDark);
      },
    );

    if (isHorizontal) {
      return SizedBox(
        height: 100,
        child: content,
      );
    } else {
      return content;
    }
  }

  /// Action Item bauen
  Widget _buildActionItem(
    BuildContext context,
    QuickAction action,
    bool isHorizontal,
    bool isDark,
  ) {
    final theme = Theme.of(context);
    final color = action.color ?? theme.primaryColor;
    final disabledColor = isDark ? Colors.grey.shade800 : Colors.grey.shade300;

    final item = GestureDetector(
      onTap: action.enabled ? action.onTap : null,
      child: Container(
        constraints: isHorizontal && maxItemWidth != null
            ? BoxConstraints(maxWidth: maxItemWidth!)
            : null,
        margin: isHorizontal
            ? const EdgeInsets.symmetric(horizontal: 4)
            : const EdgeInsets.symmetric(vertical: 4),
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: action.enabled
              ? color.withOpacity(isDark ? 0.2 : 0.1)
              : disabledColor.withOpacity(0.1),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: action.enabled
                ? color.withOpacity(0.3)
                : disabledColor.withOpacity(0.3),
            width: 1,
          ),
        ),
        child: isHorizontal
            ? _buildHorizontalLayout(action, color, isDark, theme)
            : _buildVerticalLayout(action, color, isDark, theme),
      ),
    );

    if (!action.enabled) {
      return Opacity(
        opacity: 0.6,
        child: item,
      );
    }

    return item;
  }

  /// Horizontales Layout
  Widget _buildHorizontalLayout(
    QuickAction action,
    Color color,
    bool isDark,
    ThemeData theme,
  ) {
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        // Icon
        Container(
          padding: const EdgeInsets.all(8),
          decoration: BoxDecoration(
            color: color.withOpacity(isDark ? 0.3 : 0.2),
            shape: BoxShape.circle,
          ),
          child: Icon(
            action.icon,
            size: 24,
            color: color,
          ),
        ),
        const SizedBox(height: 8),
        // Titel
        Text(
          action.title,
          style: TextStyle(
            fontSize: 12,
            fontWeight: FontWeight.bold,
            color: action.enabled
                ? isDark ? Colors.white : Colors.black87
                : theme.disabledColor,
          ),
          textAlign: TextAlign.center,
          maxLines: 2,
          overflow: TextOverflow.ellipsis,
        ),
      ],
    );
  }

  /// Vertikales Layout
  Widget _buildVerticalLayout(
    QuickAction action,
    Color color,
    bool isDark,
    ThemeData theme,
  ) {
    return Row(
      children: [
        // Icon
        Container(
          padding: const EdgeInsets.all(10),
          decoration: BoxDecoration(
            color: color.withOpacity(isDark ? 0.3 : 0.2),
            shape: BoxShape.circle,
          ),
          child: Icon(
            action.icon,
            size: 20,
            color: color,
          ),
        ),
        const SizedBox(width: 12),
        // Text-Inhalt
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Titel
              Text(
                action.title,
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                  color: action.enabled
                      ? isDark ? Colors.white : Colors.black87
                      : theme.disabledColor,
                ),
              ),
              // Beschreibung (falls vorhanden)
              if (action.description != null) ...[
                const SizedBox(height: 2),
                Text(
                  action.description!,
                  style: TextStyle(
                    fontSize: 12,
                    color: action.enabled
                        ? theme.hintColor
                        : theme.disabledColor,
                  ),
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ],
          ),
        ),
        // Pfeil (nur bei vertikaler Ansicht)
        if (action.enabled)
          Icon(
            Icons.chevron_right,
            color: theme.hintColor,
          ),
      ],
    );
  }
}

/// Vordefinierte Quick Actions für LehrerAgent
class LehrerAgentQuickActions {
  /// Unterricht planen
  static QuickAction unterrichtPlanen({
    required VoidCallback onTap,
    bool enabled = true,
  }) {
    return QuickAction(
      title: 'Unterricht planen',
      description: 'Lehrplankonforme Stundenentwürfe',
      icon: Icons.school,
      actionType: 'unterricht_planen',
      color: Colors.blue,
      enabled: enabled,
      onTap: onTap,
    );
  }

  /// Bewertung erstellen
  static QuickAction bewertungErstellen({
    required VoidCallback onTap,
    bool enabled = true,
  }) {
    return QuickAction(
      title: 'Bewertung erstellen',
      description: 'Erwartungshorizonte & Notenschlüssel',
      icon: Icons.grading,
      actionType: 'bewertung_erstellen',
      color: Colors.green,
      enabled: enabled,
      onTap: onTap,
    );
  }

  /// Schülerarbeit bewerten
  static QuickAction schuelerarbeitBewerten({
    required VoidCallback onTap,
    bool enabled = true,
  }) {
    return QuickAction(
      title: 'Schülerarbeit bewerten',
      description: 'Foto/PDF hochladen & bewerten',
      icon: Icons.photo_camera,
      actionType: 'schuelerarbeit_bewerten',
      color: Colors.orange,
      enabled: enabled,
      onTap: onTap,
    );
  }

  /// Lehrplan einlesen
  static QuickAction lehrplanEinlesen({
    required VoidCallback onTap,
    bool enabled = true,
  }) {
    return QuickAction(
      title: 'Lehrplan einlesen',
      description: 'PDF hochladen & indizieren',
      icon: Icons.menu_book,
      actionType: 'lehrplan_einlesen',
      color: Colors.purple,
      enabled: enabled,
      onTap: onTap,
    );
  }

  /// PDF hochladen
  static QuickAction pdfHochladen({
    required VoidCallback onTap,
    bool enabled = true,
  }) {
    return QuickAction(
      title: 'PDF hochladen',
      description: 'Lehrplan oder Schülerarbeit',
      icon: Icons.picture_as_pdf,
      actionType: 'pdf_upload',
      color: Colors.red,
      enabled: enabled,
      onTap: onTap,
    );
  }

  /// Bild hochladen
  static QuickAction bildHochladen({
    required VoidCallback onTap,
    bool enabled = true,
  }) {
    return QuickAction(
      title: 'Bild hochladen',
      description: 'Foto von Schülerarbeit',
      icon: Icons.image,
      actionType: 'image_upload',
      color: Colors.teal,
      enabled: enabled,
      onTap: onTap,
    );
  }

  /// Profil anzeigen
  static QuickAction profilAnzeigen({
    required VoidCallback onTap,
    bool enabled = true,
  }) {
    return QuickAction(
      title: 'Profil anzeigen',
      description: 'Lehrerprofil & Einstellungen',
      icon: Icons.person,
      actionType: 'profile_view',
      color: Colors.indigo,
      enabled: enabled,
      onTap: onTap,
    );
  }

  /// Memory anzeigen
  static QuickAction memoryAnzeigen({
    required VoidCallback onTap,
    bool enabled = true,
  }) {
    return QuickAction(
      title: 'Memory anzeigen',
      description: 'Gespeicherte Daten & Dateien',
      icon: Icons.folder,
      actionType: 'memory_view',
      color: Colors.brown,
      enabled: enabled,
      onTap: onTap,
    );
  }

  /// Prüfung erstellen
  static QuickAction pruefungErstellen({
    required VoidCallback onTap,
    bool enabled = true,
  }) {
    return QuickAction(
      title: 'Prüfung erstellen',
      description: 'Klassenarbeit, Klausur, Kurztest',
      icon: Icons.edit_document,
      actionType: 'pruefung_erstellen',
      color: Colors.deepOrange,
      enabled: enabled,
      onTap: onTap,
    );
  }

  /// Arbeitsblatt erstellen
  static QuickAction arbeitsblattErstellen({
    required VoidCallback onTap,
    bool enabled = true,
  }) {
    return QuickAction(
      title: 'Arbeitsblatt',
      description: 'Druckfertig mit Differenzierung',
      icon: Icons.assignment,
      actionType: 'arbeitsblatt_erstellen',
      color: Colors.cyan,
      enabled: enabled,
      onTap: onTap,
    );
  }

  /// Elternbrief schreiben
  static QuickAction elternbriefSchreiben({
    required VoidCallback onTap,
    bool enabled = true,
  }) {
    return QuickAction(
      title: 'Elternbrief',
      description: 'Brief für jeden Anlass',
      icon: Icons.mail_outline,
      actionType: 'elternbrief_schreiben',
      color: Colors.blueGrey,
      enabled: enabled,
      onTap: onTap,
    );
  }

  /// Zeugnis formulieren
  static QuickAction zeugnisFormulieren({
    required VoidCallback onTap,
    bool enabled = true,
  }) {
    return QuickAction(
      title: 'Zeugnistext',
      description: '3 Varianten je Note & Fach',
      icon: Icons.workspace_premium,
      actionType: 'zeugnis_formulieren',
      color: Colors.amber,
      enabled: enabled,
      onTap: onTap,
    );
  }

  /// Klassenstatistik
  static QuickAction klassenstatistik({
    required VoidCallback onTap,
    bool enabled = true,
  }) {
    return QuickAction(
      title: 'Klassenstatistik',
      description: 'Notenspiegel & Auswertung',
      icon: Icons.bar_chart,
      actionType: 'klassenstatistik',
      color: Colors.deepPurple,
      enabled: enabled,
      onTap: onTap,
    );
  }

  /// Alle Standard-Aktionen
  static List<QuickAction> allActions({
    required Map<String, VoidCallback> callbacks,
    Map<String, bool>? enabledStates,
  }) {
    return [
      unterrichtPlanen(
        onTap: callbacks['unterricht_planen'] ?? () {},
        enabled: enabledStates?['unterricht_planen'] ?? true,
      ),
      arbeitsblattErstellen(
        onTap: callbacks['arbeitsblatt_erstellen'] ?? () {},
        enabled: enabledStates?['arbeitsblatt_erstellen'] ?? true,
      ),
      pruefungErstellen(
        onTap: callbacks['pruefung_erstellen'] ?? () {},
        enabled: enabledStates?['pruefung_erstellen'] ?? true,
      ),
      bewertungErstellen(
        onTap: callbacks['bewertung_erstellen'] ?? () {},
        enabled: enabledStates?['bewertung_erstellen'] ?? true,
      ),
      schuelerarbeitBewerten(
        onTap: callbacks['schuelerarbeit_bewerten'] ?? () {},
        enabled: enabledStates?['schuelerarbeit_bewerten'] ?? true,
      ),
      elternbriefSchreiben(
        onTap: callbacks['elternbrief_schreiben'] ?? () {},
        enabled: enabledStates?['elternbrief_schreiben'] ?? true,
      ),
      zeugnisFormulieren(
        onTap: callbacks['zeugnis_formulieren'] ?? () {},
        enabled: enabledStates?['zeugnis_formulieren'] ?? true,
      ),
      klassenstatistik(
        onTap: callbacks['klassenstatistik'] ?? () {},
        enabled: enabledStates?['klassenstatistik'] ?? true,
      ),
      lehrplanEinlesen(
        onTap: callbacks['lehrplan_einlesen'] ?? () {},
        enabled: enabledStates?['lehrplan_einlesen'] ?? true,
      ),
      pdfHochladen(
        onTap: callbacks['pdf_upload'] ?? () {},
        enabled: enabledStates?['pdf_upload'] ?? true,
      ),
      bildHochladen(
        onTap: callbacks['image_upload'] ?? () {},
        enabled: enabledStates?['image_upload'] ?? true,
      ),
      profilAnzeigen(
        onTap: callbacks['profile_view'] ?? () {},
        enabled: enabledStates?['profile_view'] ?? true,
      ),
      memoryAnzeigen(
        onTap: callbacks['memory_view'] ?? () {},
        enabled: enabledStates?['memory_view'] ?? true,
      ),
    ];
  }

  /// Häufig verwendete Aktionen (für Mobile-Leiste, max. 6)
  static List<QuickAction> frequentActions({
    required Map<String, VoidCallback> callbacks,
    Map<String, bool>? enabledStates,
  }) {
    return [
      unterrichtPlanen(
        onTap: callbacks['unterricht_planen'] ?? () {},
        enabled: enabledStates?['unterricht_planen'] ?? true,
      ),
      arbeitsblattErstellen(
        onTap: callbacks['arbeitsblatt_erstellen'] ?? () {},
        enabled: enabledStates?['arbeitsblatt_erstellen'] ?? true,
      ),
      pruefungErstellen(
        onTap: callbacks['pruefung_erstellen'] ?? () {},
        enabled: enabledStates?['pruefung_erstellen'] ?? true,
      ),
      elternbriefSchreiben(
        onTap: callbacks['elternbrief_schreiben'] ?? () {},
        enabled: enabledStates?['elternbrief_schreiben'] ?? true,
      ),
      schuelerarbeitBewerten(
        onTap: callbacks['schuelerarbeit_bewerten'] ?? () {},
        enabled: enabledStates?['schuelerarbeit_bewerten'] ?? true,
      ),
      pdfHochladen(
        onTap: callbacks['pdf_upload'] ?? () {},
        enabled: enabledStates?['pdf_upload'] ?? true,
      ),
    ];
  }

  /// Nur Upload-Aktionen
  static List<QuickAction> uploadActions({
    required VoidCallback onPdfUpload,
    required VoidCallback onImageUpload,
    bool pdfEnabled = true,
    bool imageEnabled = true,
  }) {
    return [
      pdfHochladen(
        onTap: onPdfUpload,
        enabled: pdfEnabled,
      ),
      bildHochladen(
        onTap: onImageUpload,
        enabled: imageEnabled,
      ),
    ];
  }
}

/// Quick Actions Bar (für Mobile Bottom Navigation)
class QuickActionsBar extends StatelessWidget {
  final List<QuickAction> actions;
  final double height;
  final Color? backgroundColor;

  const QuickActionsBar({
    Key? key,
    required this.actions,
    this.height = 80,
    this.backgroundColor,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    return Container(
      height: height,
      color: backgroundColor ??
          (isDark ? Colors.grey.shade900 : Colors.grey.shade100),
      child: QuickActions(
        actions: actions,
        direction: Axis.horizontal,
        scrollable: true,
        maxItemWidth: 100,
      ),
    );
  }
}

/// Quick Actions Grid (für Desktop/Tablet)
class QuickActionsGrid extends StatelessWidget {
  final List<QuickAction> actions;
  final int crossAxisCount;
  final double childAspectRatio;
  final double spacing;

  const QuickActionsGrid({
    Key? key,
    required this.actions,
    this.crossAxisCount = 4,
    this.childAspectRatio = 1.2,
    this.spacing = 8,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return GridView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: crossAxisCount,
        childAspectRatio: childAspectRatio,
        crossAxisSpacing: spacing,
        mainAxisSpacing: spacing,
      ),
      itemCount: actions.length,
      itemBuilder: (context, index) {
        final action = actions[index];
        final theme = Theme.of(context);
        final isDark = theme.brightness == Brightness.dark;
        final color = action.color ?? theme.primaryColor;

        return GestureDetector(
          onTap: action.enabled ? action.onTap : null,
          child: Container(
            decoration: BoxDecoration(
              color: action.enabled
                  ? color.withOpacity(isDark ? 0.2 : 0.1)
                  : Colors.grey.withOpacity(0.1),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(
                color: action.enabled
                    ? color.withOpacity(0.3)
                    : Colors.grey.withOpacity(0.3),
                width: 1,
              ),
            ),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                // Icon
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: color.withOpacity(isDark ? 0.3 : 0.2),
                    shape: BoxShape.circle,
                  ),
                  child: Icon(
                    action.icon,
                    size: 28,
                    color: color,
                  ),
                ),
                const SizedBox(height: 8),
                // Titel
                Text(
                  action.title,
                  style: TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.bold,
                    color: action.enabled
                        ? isDark ? Colors.white : Colors.black87
                        : theme.disabledColor,
                  ),
                  textAlign: TextAlign.center,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}