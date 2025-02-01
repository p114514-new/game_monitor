# Game Monitor - record screen, keyboard, and mouse movements at the same time



### How to use

1. Install OBS studio if you don't have one.

2. Open OBS webserver settings
   ![4a44f906-45a2-4f6b-bedc-81f0951c47b1](file:///C:/Users/swx/Pictures/Typedown/4a44f906-45a2-4f6b-bedc-81f0951c47b1.png)

3. Enable OBS webserver
   ![b1d8ab29-7053-4d4a-baf6-4c0533327cb9](file:///C:/Users/swx/Pictures/Typedown/b1d8ab29-7053-4d4a-baf6-4c0533327cb9.png)

4. Check "Display connections settings" and write your host, port and password into the default params of `obs.py`
   ![0619d518-e695-4f8d-b9f1-95468151b37f](file:///C:/Users/swx/Pictures/Typedown/0619d518-e695-4f8d-b9f1-95468151b37f.png)
   ![6de99b34-2c7b-45ef-befd-8f154db67ca8](file:///C:/Users/swx/Pictures/Typedown/6de99b34-2c7b-45ef-befd-8f154db67ca8.png)
   ![439b85ec-2ff0-4a36-aa4b-055491773ac9](file:///C:/Users/swx/Pictures/Typedown/439b85ec-2ff0-4a36-aa4b-055491773ac9.png)

5. Create a scene called "screen" and configure its source as screen capture
   ![fd524a5c-24b1-4102-87b2-373cc8ad7961](file:///C:/Users/swx/Pictures/Typedown/fd524a5c-24b1-4102-87b2-373cc8ad7961.png)

6. Right click the OBS monitor and select "Window Projection" to enable correct full-screen capturing.
   
   ![f2403445-378a-4472-a95b-45ed7d7dba87](file:///C:/Users/swx/Pictures/Typedown/f2403445-378a-4472-a95b-45ed7d7dba87.png)

7. You are all done! Before you start your game, run `obs.py` in your IDE or `python obs.py` in terminal to start capturing. Videos will be stored in ./recordings, mouse and keyboard logs will be stored in the same directory as obs.py.


