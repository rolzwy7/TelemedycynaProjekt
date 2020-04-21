from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need
# fine tuning.

buildOptions = dict(
    packages = ["matplotlib"],
    excludes = [
        "xml",
        "xmlrpc",
        "setuptools",
        "concurrent",
        "curses",
        "email",
        "html",
        "http",
        "multiprocessing",
        "pytz",
    ],
    include_files = [
        ("E:\\venvs\\cx_freeze_env\\Lib\\site-packages\\mpl_toolkits", "lib\\mpl_toolkits"),
        ("data", "data"),
        ("WindowsTestStart.bat", "WindowsTestStart.bat"),
        ]
    )

base = 'Console'

executables = [
    Executable('main.py', base=base)
]

setup(
    name='TelemedycynaProjekt',
    version = '1.0',
    description = 'Telemedycyna Projekt - Bartosz Nowakowski, Maciej Śliwiński - Teleinformatyka sem. VI',
    options = dict(build_exe = buildOptions),
    executables = executables
)

