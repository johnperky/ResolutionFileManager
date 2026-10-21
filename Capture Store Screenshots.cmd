@echo off
cd /d "%~dp0"
echo Local screenshot batch. Leave the desktop free until this finishes.
echo Existing candidates are resumed. No media operations or conversions run.
python tools\batch_store_screenshots.py %* > "%TEMP%\rfm-screenshot-batch.log" 2>&1
if errorlevel 1 (
  echo Batch stopped. Previous screenshots are preserved.
) else (
  echo Batch finished. Candidates still need visual approval.
)
echo Log: %TEMP%\rfm-screenshot-batch.log
pause
