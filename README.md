# pyghotess
Python / Ghostscript / Tesseract for fast multi-threaded customizable image PDF OCR processing with real-time page-per-page result feed.

## Description
This component allows more fine-tuning, control and parallelisation of Tesseract OCR processing then other available solutions (apache Tika for example).
It is only applicable to PDF files though.

- Ghostscript for fast & precise page image extraction
- Tesseract for high-quality image OCR processing
- Python for gluing it together and provide a nice asynchronous web interface (Rest or websocket API)

### Advantages
- Configure the parameters to the task at hand : is the original material of good quality ? Is the orientation bad ? The resolution ?
- Distribute the OCR processing over multiple CPU's

### Disadvantage
- Less flexible: only works with image-PDF files

### Other ideas
- Per-page configuration
- Faster first-page result (TTFR: time-to-first-result)
- Improve and parallelize first step (ghostscript image creation)

## Installation
From the root directory of in your local copy (after cloning the repository):
```bash
# poetry
> poetry install
```
### Poetry installation
Poetry installs a local, isolated python environment, to avoid conflicts with your system's python modules. See [here](https://python-poetry.org/docs/).

A recent [python](https://www.python.org/downloads/) version (>=3.7) will also be needed.

## Usage
Can be used with **poetry**, **docker** CLI or as **API** (Poetry or Docker).

### CLI usage
```bash
Usage: run.py [OPTIONS] COMMAND [ARGS]...

Options:
  -d, --debug TEXT  Activate debugging flag
  --help            Show this message and exit.

Commands:
  extract  EXTRACT Extract PDF files to PNG images
      -f, --file TEXT     Input image-PDF file
      -o, --out-dir TEXT  Root directory for temp directory

  ocr      OCR Parse directory with PNG images by OCR processing and output...
      -d, --dir TEXT  Directory with image files

  process  PARSE Parse Image PDF file, output resulting text.
      -f, --file TEXT  Input image-PDF file

# Example (with poetry)
$ poetry run ./run.py process -f test2.pdf
```

### API Usage
By default, the API binds to port 5501 (settings are set by environment variables or by using a config file, see `config_default.toml`)
```bash
# Run locally in debug mode
> poetry run api --debug
# Run locally with config file
> poetry run api --config config.toml
```

### Websocket usage
Doc to be done, see `/tests/behave/steps/ws_steps.py` for an example implentation.

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## Updating docker
The `docker_tool.sh` script allows for reasy updating of docker hub images. Update with your own repo settings if needed.

```
# Build
$ ./docker_tool.sh build [VERSION]
# Test
$ ./docker_tool.sh test [VERSION]
# Publish
$ ./docker_tool.sh publish [VERSION]
# Tag latest version
$ ./docker_tool.sh latest [VERSION]
```


### Testing
Pyghotess uses behave BDD testing. Features and steps are specified in the `tests/behave` folder and can be run this way:
```bash
$ poetry run behave tests/behave
```
