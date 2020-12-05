# pyghotess
Python / Ghostscript / Tesseract fast image PDF OCR processing

This component allows more fine-tuning, control and parallelisation of Tesseract OCR processing then other available solutions (apache Tika for example).
It is only applicable to PDF files though.

## Advantages
- Configure the parameters to the task at hand : is the original material of good quality ? Is the orientation bad ? The resolution ?
- Distribute the OCR processing over multiple CPU's

## Disadvantage
- Less flexible: only works with PDF files

## Other ideas
- Streaming of output : get first pages while other pages are still processed

## Usage
Can be used with **poetry**, **docker** CLI or as **API** (Poetry or Docker).


