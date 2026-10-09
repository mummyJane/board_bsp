# Load the ESP-IDF environment into the current PowerShell session.
#   . .\tools\idf_env.ps1
# Override the defaults by setting IDF_PATH / IDF_PYTHON_ENV_PATH before running.

if (-not $env:IDF_PATH) {
    $env:IDF_PATH = "D:\wirkflow\esp_test\tools\esp-idf-6.1"
}
if (-not $env:IDF_TOOLS_PATH) {
    $env:IDF_TOOLS_PATH = "$env:USERPROFILE\.espressif"
}
if (-not $env:IDF_PYTHON_ENV_PATH) {
    $env:IDF_PYTHON_ENV_PATH = "$env:IDF_TOOLS_PATH\python_env\idf6.1_py3.13_env"
}

. "$env:IDF_PATH\export.ps1"
idf.py --version
