@echo off
if exist test rmdir /s /q test
robocopy src test\src /E /NFL /NDL /NJH /NJS
robocopy . test /NFL /NDL /NJH /NJS start.bat
if not exist test\src\data mkdir test\src\data
cd /d test
if exist start.bat start start.bat
