# smart-sight

## Dependencies
1. Python 3.8 or higher. Please, install from official website or another way.
2. PIP. [Windows instruction](https://phoenixnap.com/kb/install-pip-windows)
3. FFMPEG. [Windows instruction](https://phoenixnap.com/kb/ffmpeg-windows)
4. git. [Instructions](https://github.com/git-guides/install-git)

## Workflow
Be careful, on Windows machine change `python` command to `py`: https://docs.python.org/3/using/windows.html#from-the-command-line

### 1. Connect the sight(servo and camera) to computer.

### 2. Clone the repo
```bash
git clnne https://github.com/klymya/smart-sight.git && cd smart-sight
```

### 3. Install requirement libs
```bash
python -m pip install -r requirements.txt
```

### 4. Inference
Run main loop:
```bash
python src/main.py
```

The default parameters should be enough. But you can specify any parameter. Parameters description:
```bash
python scr/main.py -h
```
Please, pay attention to `--input` field. It specifies the camera index - the int number, e.g.:
```bash
python src/main.py --input 0
```
or 
```bash
python src/main.py --input 1
```


### 5. Camera calibration if needed
Record video or set of images with calibration pattern. After that find the camera parameters using `src/camera_calibration.py`.
You can save the params in `camera_params` folder.

## Camera parameters
### Logitec c170
- Model ID: UVC Camera VendorID_1133 ProductID_2091
- Unique ID: 0x14423000046d082b
- `logi_c170_0.csv` and `logi_c170_1.csv` - the files used different videos from one camera and have slightly different results.

### Logitec 270*
- `logi_c270.csv`

\* - the default camera