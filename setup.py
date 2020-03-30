from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need
# fine tuning.

buildOptions = dict(
    packages = ["matplotlib"],
    excludes = [],
    include_files = [("E:\\venvs\\cx_freeze_env\\Lib\\site-packages\\mpl_toolkits", "lib\\mpl_toolkits")]
    )

base = 'Console'

executables = [
    Executable('telemed.py', base=base)
]

setup(name='TelemedycynaProjekt',
      version = '1.0',
      description = '',
      options = dict(build_exe = buildOptions),
      executables = executables)
