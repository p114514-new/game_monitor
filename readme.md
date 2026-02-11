# Game Monitor

### How to use

1. Install OBS studio **30.1.0** if you don't have one. Make sure the version is 30.1.0. This application is not guaranteed to fit for other versions.

2. Open OBS webserver settings
   ![38eb221a-5602-4b80-a073-754374a6374d](./assets/38eb221a-5602-4b80-a073-754374a6374d.png)
   
3. Enable OBS webserver
   ![1603a009-64f2-4244-884b-d8d1f148413d](./assets/1603a009-64f2-4244-884b-d8d1f148413d.png)

4. Check "Display connections settings" for your host, port and password (modify first if you wish). Copy these information into the upper part of the game monitor panel.
   ![d930f332-2a2b-49ac-a345-7af2b0c9cddc](./assets/d930f332-2a2b-49ac-a345-7af2b0c9cddc.png)
   ![38470080-2078-415b-9346-5ef564283430](./assets/38470080-2078-415b-9346-5ef564283430.png)
   ![connections](./assets/connections.png)

5. Create a scene called "screen" (or any name you want, but make sure the name is consistent with the settings in step 6) and configure its source as screen capture. Double-check if the screen capture is enabled or you will record an empty dark screen.
   ![c2de43aa-9448-4fb5-a7a3-22e23b329b02](./assets/c2de43aa-9448-4fb5-a7a3-22e23b329b02.png)

6. Input the scene name and select the folder where the application would save your video and action records. Make sure you are selecting a disk that has enough space left, as the videos can be quite large under default settings (4-5GB per hour)
   ![recordings](./assets/recordings.png)

7. **First left click the upper part (recording preview screen) of the obs panel. (should have a red edge if selected)** Then right click the same part (the preview screen) and select "Render as source resolution" (使用此源的尺寸作为输出分辨率) to enable correct full-screen capturing.
   ![404c1f66-938d-440f-b58e-59e2ff2a6f5c](./assets/404c1f66-938d-440f-b58e-59e2ff2a6f5c.png)

8. Set video format to mkv, video encoder to NVIDIA NVENC HEVC, bitrate to 8000 Kbps, fps to 30
   ![188a8460f94a62adb92de72d7ba59f55](./assets/188a8460f94a62adb92de72d7ba59f55.png)
   ![322ce2fb9c64597b3dc89f57eafc68af](./assets/322ce2fb9c64597b3dc89f57eafc68af.png)
   ![84bd341e59587877e3491dd0b15c0352](./assets/84bd341e59587877e3491dd0b15c0352.png)

9. You are all done! Before you start your game, **make sure obs is running in the background**, and click the blue 'start recording' button to start capturing. This will automatically start the obs. A red dot will appear on the obs icon if the setup is successful. The red 'stop recording' button stops all recordings, including the obs.

