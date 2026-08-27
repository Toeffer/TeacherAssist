"""Exercises parse_multipart_parts / parse_multipart in tool_server.py:400-441.

Covers the Stufe-0 bugfix (task 0.2): non-file fields alongside a file part, the
RFC-2046 boundary-delimiter fix (splitting on b"\\r\\n--" + boundary instead of a
bare "--boundary" so a boundary-shaped substring inside file *content* no longer
mis-parses the body), field-value truncation, and graceful handling of malformed
bodies.
"""

import tool_server


BOUNDARY = "TeacherAssistTestBoundary123"


def _multipart_body(parts, boundary=BOUNDARY):
    """Builds a well-formed multipart/form-data body from a list of part specs.

    Each part spec is a dict with either:
      - {"name": ..., "filename": ..., "content": bytes, "content_type": ...}  (file part)
      - {"name": ..., "value": str}                                           (field part)
    """
    chunks = []
    for part in parts:
        if "filename" in part:
            disposition = f'Content-Disposition: form-data; name="{part["name"]}"; filename="{part["filename"]}"'
            content_type = part.get("content_type", "application/octet-stream")
            head = ("--" + boundary + "\r\n" + disposition + "\r\n" + f"Content-Type: {content_type}" + "\r\n\r\n").encode()
            chunks.append(head + part["content"] + b"\r\n")
        else:
            disposition = f'Content-Disposition: form-data; name="{part["name"]}"'
            head = ("--" + boundary + "\r\n" + disposition + "\r\n\r\n").encode()
            value = part["value"]
            value_bytes = value if isinstance(value, bytes) else value.encode("utf-8")
            chunks.append(head + value_bytes + b"\r\n")
    chunks.append(("--" + boundary + "--\r\n").encode())
    return b"".join(chunks)


def test_parse_multipart_parts_round_trips_file_and_fields():
    """A body with one file part and two text fields must yield both: the file in
    `files` (unchanged shape from the pre-refactor parse_multipart) and the two
    text fields in `fields`. parse_multipart() must keep returning just the files
    list, so /api/v1/upload and /api/v1/ocr-image callers are unaffected."""
    body = _multipart_body(
        [
            {"name": "file", "filename": "photo.jpg", "content": b"\xff\xd8\xff\xe0FAKEJPEG", "content_type": "image/jpeg"},
            {"name": "classification", "value": "hausaufgabe"},
            {"name": "language", "value": "de"},
        ]
    )

    files, fields = tool_server.parse_multipart_parts(body, BOUNDARY)

    assert files == [("photo.jpg", b"\xff\xd8\xff\xe0FAKEJPEG")]
    assert fields == {"classification": "hausaufgabe", "language": "de"}

    # Backwards-compatible wrapper still returns only the files list, same shape.
    assert tool_server.parse_multipart(body, BOUNDARY) == files


def test_boundary_like_bytes_inside_file_content_do_not_split_the_part():
    """Regression test for the RFC 2046 fix in tool_server.py: a boundary delimiter
    is always preceded by CRLF. The old implementation split on a bare
    ("--" + boundary).encode(), so file content that happens to contain that literal
    substring (without a preceding CRLF) would be sliced in the middle, corrupting
    the uploaded bytes. The new implementation splits on b"\\r\\n--" + boundary, so a
    same-looking substring with no preceding CRLF is just ordinary content."""
    boundary = "XBOUND"
    # Content deliberately embeds "--XBOUND" as raw bytes, with NO preceding \r\n,
    # so a naive split on ("--" + boundary) alone would wrongly cut the file here.
    tricky_content = b"HEADER--XBOUNDTRAILER"
    body = _multipart_body(
        [{"name": "file", "filename": "tricky.bin", "content": tricky_content}],
        boundary=boundary,
    )

    files, fields = tool_server.parse_multipart_parts(body, boundary)

    assert files == [("tricky.bin", tricky_content)]
    assert fields == {}


def test_field_without_filename_lands_in_fields_not_files():
    """A part whose Content-Disposition carries name= but no filename= is a plain
    form field and must appear only in `fields`, never in `files` (tool_server.py
    parse_multipart_parts: `if filename: files.append(...) elif name: fields[...] = ...`)."""
    body = _multipart_body([{"name": "subject", "value": "Mathematik"}])

    files, fields = tool_server.parse_multipart_parts(body, BOUNDARY)

    assert files == []
    assert fields == {"subject": "Mathematik"}


def test_field_value_longer_than_4096_bytes_is_truncated():
    """Per the parse_multipart_parts docstring, each field value is truncated to
    4096 bytes before being UTF-8 decoded (errors='replace'), so a misbehaving or
    malicious client cannot smuggle an arbitrarily large sidecar field."""
    long_value = "a" * 5000
    body = _multipart_body([{"name": "notes", "value": long_value}])

    _, fields = tool_server.parse_multipart_parts(body, BOUNDARY)

    assert len(fields["notes"].encode("utf-8")) <= 4096
    assert fields["notes"] == "a" * 4096


def test_malformed_body_returns_what_it_can_without_raising():
    """A body missing its terminating boundary and containing a part with no
    \\r\\n\\r\\n header/body separator must not raise; parse_multipart_parts should
    simply skip what it cannot parse and return whatever valid parts it found."""
    boundary = "MALFORMED"
    good_part = (
        f"--{boundary}\r\n"
        'Content-Disposition: form-data; name="ok"\r\n\r\n'
        "fine\r\n"
    ).encode()
    # No header/body separator at all in this part.
    broken_part = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"broken\"").encode()
    # Body deliberately omits the closing "--boundary--".
    body = good_part + broken_part

    files, fields = tool_server.parse_multipart_parts(body, boundary)

    assert files == []
    assert fields == {"ok": "fine"}
