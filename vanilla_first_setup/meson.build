pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
moduledir = join_paths(pkgdatadir, 'vanilla_first_setup')
gnome = import('gnome')

blueprints = custom_target('blueprints',
  input: files(
    'gtk/default-conn-check.blp',
    'gtk/default-hostname.blp',
    'gtk/default-theme.blp',
    'gtk/default-user.blp',
    'gtk/default-welcome.blp',
    'gtk/dialog.blp',
    'gtk/done.blp',
    'gtk/layout-applications.blp',
    'gtk/layout-preferences.blp',
    'gtk/layout-yes-no.blp',
    'gtk/post-script.blp',
    'gtk/progress.blp',
    'gtk/tour.blp',
    'gtk/window.blp',
  ),
  output: '.',
  command: [find_program('blueprint-compiler'), 'batch-compile', '@OUTPUT@', '@CURRENT_SOURCE_DIR@', '@INPUT@'],
)

gnome.compile_resources('vanilla-first-setup',
  'vanilla-first-setup.gresource.xml',
  gresource_bundle: true,
  install: true,
  install_dir: pkgdatadir,
  dependencies: blueprints,
)

python = import('python')

conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').path())
conf.set('VERSION', meson.project_version())
conf.set('localedir', join_paths(get_option('prefix'), get_option('localedir')))
conf.set('pkgdatadir', pkgdatadir)

configure_file(
  input: 'vanilla-first-setup.in',
  output: 'vanilla-first-setup',
  install_mode: 'rwxr-xr-x',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir'),
  install_mode: 'rwxr-xr-x'
)

configure_file(
  input: 'vanilla-first-setup-processor.in',
  output: 'vanilla-first-setup-processor',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir')
)

subdir('utils')
subdir('defaults')
subdir('layouts')
subdir('views')

vanilla_first_setup_sources = [
  '__init__.py',
  'main.py',
  'window.py',
  'dialog.py',
]

install_data(vanilla_first_setup_sources, install_dir: moduledir)