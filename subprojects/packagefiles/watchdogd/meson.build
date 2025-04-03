project(
  'watchdogd', 'c',
  version: '4.1',
  meson_version: '>=1.1'
)
mod = import('unstable-external_project')
run_command(files('autogen.sh'), check: true)
p = mod.add_project(
  'configure',
  configure_options : ['--prefix=@PREFIX@',
		       '--libdir=@PREFIX@/@LIBDIR@',
		       '--includedir=@PREFIX@/@INCLUDEDIR@',
		       '--enable-static',
		       '--disable-shared',
		       '--enable-pic'],
)

libwdog = p.dependency('wdog')
meson.override_dependency('libwdog', libwdog)
