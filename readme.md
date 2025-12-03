# Game Monitor

# Game Monitor - record screen, keyboard, and mouse movements at the same time



### How to use

1. Install OBS studio if you don't have one.

2. Open OBS webserver settings
   ![38eb221a-5602-4b80-a073-754374a6374d](./assets/38eb221a-5602-4b80-a073-754374a6374d.png)
   
   

3. Enable OBS webserver
   ![1603a009-64f2-4244-884b-d8d1f148413d](./assets/1603a009-64f2-4244-884b-d8d1f148413d.png)

4. Check "Display connections settings" and write your host, port and password into the default params of `obs.py`
   ![d930f332-2a2b-49ac-a345-7af2b0c9cddc](./assets/d930f332-2a2b-49ac-a345-7af2b0c9cddc.png)
   ![38470080-2078-415b-9346-5ef564283430](./assets/38470080-2078-415b-9346-5ef564283430.png)
   ![6dfd4502-7d4a-4f39-95e8-46fc4a20a6da](./assets/6dfd4502-7d4a-4f39-95e8-46fc4a20a6da.png)

5. Create a scene called "screen" and configure its source as screen capture
   ![c2de43aa-9448-4fb5-a7a3-22e23b329b02](./assets/c2de43aa-9448-4fb5-a7a3-22e23b329b02.png)

6. Right click the OBS monitor and select "Window Projection" to enable correct full-screen capturing.
   ![404c1f66-938d-440f-b58e-59e2ff2a6f5c](./assets/404c1f66-938d-440f-b58e-59e2ff2a6f5c.png)

7. You are all done! Before you start your game, run `obs.py` in your IDE or `python obs.py` in terminal to start capturing. Videos will be stored in ./recordings, mouse and keyboard logs will be stored in the same directory as obs.py.

