project('popup-ai',
  version: '0.1.0',
  meson_version: '>= 0.64.0',
  default_options: [ 'warning_level=2', ],
)

# Import modules
i18n = import('i18n')

# Python installation
python = import('python').find_installation('python3')
prefix = get_option('prefix')
bindir = prefix / get_option('bindir')
datadir = prefix / get_option('datadir')
pkgdatadir = datadir / meson.project_name()

# Application ID
application_id = 'io.github.chenkeao.PopupAI'

# Configuration data
conf = configuration_data()
# Always use system python, not venv python
conf.set('PYTHON', '/usr/bin/python3')
conf.set('VERSION', meson.project_version())
conf.set('localedir', prefix / get_option('localedir'))
conf.set('pkgdatadir', pkgdatadir)
conf.set('bindir', bindir)
conf.set('application_id', application_id)

# Install Python modules
py_install_dir = python.get_install_dir()
install_subdir('src',
  install_dir: py_install_dir
)

# Install main executable
configure_file(
  input: 'data' / 'popup-ai.in',
  output: 'popup-ai',
  configuration: conf,
  install: true,
  install_dir: bindir,
  install_mode: 'rwxr-xr-x'
)

# Desktop file
desktop_file = configure_file(
  input: 'data' / application_id + '.desktop.in',
  output: application_id + '.desktop',
  configuration: conf,
  install: true,
  install_dir: datadir / 'applications'
)

# GSchema
install_data(
  'data' / application_id + '.gschema.xml',
  install_dir: datadir / 'glib-2.0' / 'schemas'
)

# Application icon
install_data(
  'data' / 'icon.svg',
  install_dir: datadir / 'icons' / 'hicolor' / 'scalable' / 'apps',
  rename: application_id + '.svg'
)

# AppStream metainfo
install_data(
  'data' / application_id + '.metainfo.xml',
  install_dir: datadir / 'metainfo'
)
