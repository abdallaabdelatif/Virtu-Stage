# VR Presentation Library Contract

Last verified: 2026-06-28

The VR client uses the same authenticated central-backend API as the dashboard.
Cloudflare R2 remains private; Unity never receives R2 credentials or permanent
public URLs.

## Flow

```text
Open Public Speaking
  -> GET /api/files                  (small metadata list only)
Select one ready presentation
  -> GET /api/files/{file_id}/slides (ordered signed image URLs)
  -> download/cache the PNG files
  -> display slide 1..N
```

Both requests require `Authorization: Bearer <access_token>`. Ownership is
checked by the central backend.

## List presentations

```http
GET /api/files
Authorization: Bearer <access_token>
```

Example response:

```json
[
  {
    "file_id": "1ab2c3d4-0000-4000-8000-000000000000",
    "original_name": "lecture.pptx",
    "content_type": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "size_bytes": 1523400,
    "upload_status": "ready",
    "processing_status": "ready",
    "slide_count": 20,
    "processing_error": null,
    "created_at": "2026-06-28T12:00:00Z"
  }
]
```

Do not request images while rendering the list. Show/select only records whose
`processing_status` is `ready`. The other values are `queued`, `processing`, and
`failed`.

## Fetch a selected presentation

```http
GET /api/files/{file_id}/slides
Authorization: Bearer <access_token>
```

Example response:

```json
{
  "file_id": "1ab2c3d4-0000-4000-8000-000000000000",
  "original_name": "lecture.pptx",
  "processing_status": "ready",
  "slide_count": 2,
  "slides": [
    {
      "number": 1,
      "width": 1920,
      "height": 1080,
      "size_bytes": 184221,
      "url": "https://<signed-r2-url>",
      "expires_at": "2026-06-28T13:00:00Z"
    },
    {
      "number": 2,
      "width": 1920,
      "height": 1080,
      "size_bytes": 173009,
      "url": "https://<signed-r2-url>",
      "expires_at": "2026-06-28T13:00:00Z"
    }
  ]
}
```

Slides are ordered by `number`. Download them immediately after selection and
cache them for the active session. If the URLs expire before download finishes,
request the manifest again. A non-ready presentation returns HTTP `409`; an
unowned presentation returns `403`.

Generated objects use:

```text
presentations/{user_id}/{file_id}/slides/0001.png
presentations/{user_id}/{file_id}/slides/0002.png
...
```

Deleting the presentation from the dashboard permanently deletes its generated
slide images, its original PDF/PPTX, and its database metadata.
