# Сборка debug-APK через Docker (образ kivy/buildozer).
# Запуск из PowerShell: .\build.ps1
#
# Тома:
#   buildozer_global - Android SDK/NDK (монтируется в /root и /home/user)
#   cyclic_build     - кэш сборки проекта
#   cyclic_android   - debug-ключ подписи (~/.android), чтобы APK ставились поверх друг друга
# Проект должен монтироваться в /home/user/hostcwd: кэш собран с этим путём.
# `yes |` отвечает на вопрос buildozer про запуск от root.

Set-Location $PSScriptRoot

docker run --rm --entrypoint /bin/bash `
    -v "${PWD}:/home/user/hostcwd" `
    -v buildozer_global:/root/.buildozer `
    -v buildozer_global:/home/user/.buildozer `
    -v cyclic_build:/home/user/hostcwd/.buildozer `
    -v cyclic_android:/root/.android `
    -w /home/user/hostcwd `
    kivy/buildozer -c 'export PATH=/home/user/.venv/bin:$PATH; yes | buildozer android debug'

if ($LASTEXITCODE -eq 0) {
    Get-ChildItem bin -Filter *.apk | Select-Object Name, Length, LastWriteTime
} else {
    Write-Error "Сборка завершилась с кодом $LASTEXITCODE"
}
