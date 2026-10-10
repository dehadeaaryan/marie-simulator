# Social link preview

`web/static/marie-social-preview.png` is the opaque 1200 × 630 PNG link-preview image. It uses the simulator's dark palette, orange period, assembly example, and accumulator display. Generated with the built-in image generation tool; the existing AD logo is unchanged and is not reproduced in this artwork.

`web/src/app.html` includes Open Graph and Twitter card metadata in the initial HTML, with absolute production URLs. Deploy the updated frontend to publish the image and metadata. Message apps may cache previews; an existing message may retain its old card. An actual iMessage preview must be checked after deployment.

## Generation prompt

undefined
