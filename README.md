# Quake 2 MD2 Importer for Blender

A Blender addon to import Quake 2 (`.md2`) models, preserving geometry, UV mapping, and animations.

Compatible with Blender 4.2+ (Extensions system) and Blender 5.0+.

## Features

- **Geometry**: Imports vertices and faces properly.
- **UV Mapping**: Preserves original texture coordinates.
- **Animation Support**:
  - **Standard Mode**: Imports animations as absolute Shape Keys with a driven timeline.
  - **One Object Per Frame**: Option to generate a separate object for every frame (useful for selecting specific static poses).
- **Texture Handling**: 
  - Automatically searches for textures in the same directory.
  - Supports `.png`, `.jpg`, `.jpeg`, `.tga`.
  - **Note**: `.pcx` files are ignored due to compatibility issues; please convert them to `.png`.

## Installation

1. Download the repository source.
2. Open Blender.
3. Go to `Edit > Preferences > Get Extensions`.
4. Click the arrow/options menu and select **"Install from Disk..."**.
5. Select the `md2_import.zip` file (if you packaged it) or the `md2_import` folder inside the repository.

## Usage

1. Go to `File > Import > Quake 2 (.md2)`.
2. Browse to your `.md2` file.
3. **Options**:
   - **One Object Per Frame**: Check this if you want to inspect frames individually as separate objects.
4. Click **Import MD2**.
5. Press **Play** (Spacebar) to view the animation (in Standard Mode).

## License

GPL-2.0-or-later
