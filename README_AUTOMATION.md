# Puzzle Workflow Automation

This document describes the new automation features for the Name That Yankee puzzle workflow.

## Overview

The automation system transforms your 7-step manual puzzle addition process into a streamlined automated workflow, reducing the time from ~15 minutes per puzzle to ~2 minutes.

## New Features

### 1. Automated Image Processing
- Convert PNG screenshots to WEBP format automatically
- Optimize images for web performance
- Handle proper naming conventions
- Validate image quality

### 2. Player Image Search
- Automatically search for player images online
- Prioritize baseball card images
- Download and process best candidates
- Fallback search strategies

### 3. Git Integration
- Optional automatic commit and push
- Descriptive commit messages
- Safe git operations with error handling

### 4. Configuration Management
- Persistent settings for automation preferences
- Image quality and processing options
- Git automation toggles
- Validation and error checking

## Usage

### Single Puzzle Automation

Process a single puzzle screenshot:

```bash
# Interactive mode
python page-generator/main.py --automate-workflow

# Command line with screenshot path
python page-generator/main.py --automate-workflow /path/to/screenshot.png

# With specific date
python page-generator/main.py --automate-workflow /path/to/screenshot.png 2025-03-06
```

### Batch Processing

Process multiple screenshots from a directory:

```bash
# Interactive mode
python page-generator/main.py --batch-automate

# Command line with directory
python page-generator/main.py --batch-automate /path/to/screenshots/

# With date range
python page-generator/main.py --batch-automate /path/to/screenshots/ --date-range 2025-03-01 2025-03-31
```

### Configuration Management

Configure automation settings:

```bash
python page-generator/main.py --config
```

Configuration options include:
- Image quality settings
- Auto-commit/auto-push toggles
- Search preferences
- Workflow options

## Workflow Comparison

### Before (Manual Workflow)
1. Screenshot puzzle from X.com
2. Convert PNG to WEBP using squoosh website
3. Manually name and place clue image
4. Run Python script for puzzle solving
5. Search for player image manually
6. Convert and name player image
7. Manual git operations

### After (Automated Workflow)
1. Take screenshot (or let automation grab it)
2. Run single automation command
3. Done! (Optional: Review and git push)

## Configuration File

The automation creates an `automation_config.json` file with default settings:

```json
{
  "image_processing": {
    "quality": 85,
    "max_width": 800,
    "max_height": 600,
    "min_width": 200,
    "min_height": 200
  },
  "player_image_search": {
    "max_results": 10,
    "timeout_seconds": 30,
    "prefer_baseball_cards": true,
    "fallback_enabled": true
  },
  "git_integration": {
    "auto_commit": false,
    "auto_push": false,
    "remote": "origin",
    "branch": "master"
  },
  "workflow": {
    "auto_approve_player": true,
    "skip_manual_review": true,
    "cleanup_temp_files": true,
    "batch_processing_enabled": true
  }
}
```

## Error Handling

The automation includes comprehensive error handling:

- **Image processing failures**: Validates image quality and format
- **Player search failures**: Multiple fallback strategies
- **Git operation failures**: Safe rollback and error reporting
- **API quota exceeded**: Graceful handling with clear error messages

## Dependencies

The automation uses existing dependencies plus:
- `requests` - For image downloads
- `Pillow` - For image processing (already included)

## Testing

Run the automation test suite:

```bash
python test_automation.py
```

## Backward Compatibility

The automation is fully backward compatible:
- All existing functionality preserved
- Manual workflow still available
- No breaking changes to existing API
- Automation as opt-in feature

## Troubleshooting

### Common Issues

1. **"Automation modules not available"**
   - Ensure all dependencies are installed
   - Check Python path includes page-generator directory

2. **Image search fails**
   - Check internet connection
   - Verify player name spelling
   - Try fallback search options

3. **Git operations fail**
   - Verify git repository status
   - Check remote connection
   - Ensure proper permissions

### Debug Mode

Enable debug logging by setting:
```json
{
  "logging": {
    "level": "DEBUG"
  }
}
```

## Migration Guide

To migrate from manual to automated workflow:

1. **Test automation**: Start with auto-commit disabled
2. **Configure settings**: Adjust image quality and git preferences
3. **Run first automation**: Process a recent puzzle
4. **Verify results**: Check generated files and git history
5. **Enable auto-commit**: Once comfortable with the process

## Future Enhancements

Planned improvements:
- X.com API integration for automatic screenshot capture
- Enhanced image quality assessment
- Multi-source player image search
- Advanced git workflow options
- Web-based configuration interface

## Support

For issues or questions:
1. Check the troubleshooting section
2. Run the test suite to verify installation
3. Review logs for detailed error messages
4. Check existing manual workflow for comparison
