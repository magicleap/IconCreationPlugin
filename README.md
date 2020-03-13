# Portal Icon Plugin

## Summary

This plugin aims to make Icon creation an easy process with a way to accurately visualize the Icon you've created.

Use this plugin to build and validate that your Icon will meet the submission guidelines. Then use the `Icon Review` app to preview the Icon in it's many interaction states on device.


## Dependencies

**Maya Module**
- Maya 2017+
- Windows or MacOS
- The Lab, with the latest MLSDK

**Icon Review App**
- Magic Leap 1 device
- Latest OS up to date to download from Magic Leap World
- Internet access - strictly to pass Icons from your computer to the Magic Leap 1


## Installing

1. Download the [release]("https://github.com/magicleap/IconCreationPlugin/releases").
2. Once the zip archive is downloaded, unzip the contents to your Maya `modules` folder.
3. Next time you open Maya, a new menu named `Magic Leap` will show up. Use this to create or edit Portal Icons.

## Usage

### Creating an Icon

1. Open up Maya.
2. Click on the `Magic Leap` menu item, and click on `Create New Portal Icon..`.
3. A new dialog will open, use this to setup your initial Icon source file scene. Set a file path, and click `Create`.
4. The Icon template will then be imported into the scene, and the `Icon Settings Widget` will open up.
5. Use the settings panel to build out all needed parts for the Icon.
    - Use `Configure Scene` to make sure the correct units are being used for Icon components.
    - Use `Assign Materials` to load in your diffuse/base color texture maps for each assigned mesh material.
    - Use `Setup Animation` to set the in/out times for each optional take.
    - Use `Validate and Export` to build out the Icon and validate it's contents. The output is a zip archive.
6. Once all sections have a green check, your Icon is ready to export and put in your app.
7. Optionally, you can also preview the Icon on device.


### Previewing the Icon on Device

1. Connect your Magic Leap 1 device to your computer.
    - You can double check your device is connected using `The Lab`.
2. Make sure the Magic Leap 1 and your computer are on the same network for the `Icon Review` app.
3. Make sure you download the app from Magic Leap World.
4. Open `Icon Review` on device. The first prism you see will give you the connection details to your computer. Keep this open to keep the connection live to Maya.
5. Go back to Maya, and click on `Preview on Device`, and you should see a new prism open up with your Icon.
6. The control responds to the different sections of the preview. Use it to test the different states of your Icon.


## Links

- [Developer Portal]("https://developer.magicleap.com")
- [Submission Guidelines]("https://developer.magicleap.com/learn/guides/content-guidelines")
- [The Lab]("https://developer.magicleap.com/downloads/lab")
- [Magic Leap Forums]("https://forum.magicleap.com/hc/en-us/community/topics")