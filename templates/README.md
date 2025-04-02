# Video Templates Directory

This directory contains video templates that can be used for generating YouTube Shorts.

## Using Templates

1. Place your video template files (MP4 format) in this directory
2. Templates should be in 9:16 aspect ratio (1080x1920 pixels) for best results
3. Templates should be at least 10 seconds long
4. Name your templates descriptively (e.g., `nature_background.mp4`, `urban_timelapse.mp4`)

## Batch Processing with CSV

You can use the CSV template to generate multiple videos at once. The template file is located at `templates/video_ideas_template.csv`.

### CSV Format

The CSV file should have the following columns:

- `topic`: The main idea or topic for the video
- `content_style`: Style of content (educational, listicle, how_to, etc.)
- `duration`: Length of the video in seconds (10-60)
- `language`: Language code (en, es, fr, etc.)
- `visual_theme`: Visual theme (modern, minimal, vibrant, etc.)
- `template_name`: Name of the template file to use (without the .mp4 extension)

### Example

```
topic,content_style,duration,language,visual_theme,template_name
"Amazing facts about space exploration",educational,30,en,modern,default
"5 tips for productivity",listicle,25,en,minimal,default
"How to learn a new language fast",how_to,45,en,vibrant,default
```

## Default Templates

If no template is specified or the specified template doesn't exist, the system will:
1. Try to find a suitable background video in the resources directory
2. If none is found, it will create a solid color background 