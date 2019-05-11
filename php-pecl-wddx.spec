# TODO:
# - wddx: restore session support (not compiled in due DL extension check)
# - wddx doesn't require session as it's disabled at compile time:
#   if HAVE_PHP_SESSION && !defined(COMPILE_DL_SESSION)
#   see also php.spec#rev1.120.2.22
#
# Conditional build:
%bcond_without	tests		# build without tests

%define		rel		1
%define		commit	92c9c4a
%define		php_name	php%{?php_suffix}
%define		modname	wddx
Summary:	wddx extension module for PHP
Summary(pl.UTF-8):	Moduł wddx dla PHP
Name:		%{php_name}-pecl-%{modname}
Version:	1.0.0
Release:	1
License:	PHP 3.01
Group:		Development/Languages/PHP
Source0:	https://git.php.net/?p=pecl/text/wddx.git;a=snapshot;h=%{commit};sf=tgz;/php-pecl-%{modname}-%{version}-%{commit}.tar.gz
# Source0-md5:	26015cbae30cc81b4ddabd060ec94b56
URL:		https://pecl.php.net/package/wddx/
BuildRequires:	%{php_name}-cli
BuildRequires:	%{php_name}-devel >= 4:7.3
BuildRequires:	rpmbuild(macros) >= 1.666
%if %{with tests}
BuildRequires:	%{php_name}-xml
%endif
%{?requires_php_extension}
Requires:	%{php_name}-xml
Provides:	php(%{modname}) = %{version}
BuildRoot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)

%description
This is a dynamic shared object (DSO) for PHP that will add wddx
support.

%description -l pl.UTF-8
Moduł PHP umożliwiający korzystanie z wddx.

%prep
%setup -qc
mv %{modname}-*/* .

cat <<'EOF' > run-tests.sh
#!/bin/sh
export NO_INTERACTION=1 REPORT_EXIT_STATUS=1 MALLOC_CHECK_=2
exec %{__make} test \
	PHP_EXECUTABLE=%{__php} \
	PHP_TEST_SHARED_SYSTEM_EXTENSIONS="xml" \
	RUN_TESTS_SETTINGS="-q $*"
EOF
chmod +x run-tests.sh

xfail() {
	local t=$1
	test -f $t
	cat >> $t <<-EOF

	--XFAIL--
	Skip
	EOF
}

while read line; do
	t=${line##*\[}; t=${t%\]}
	xfail $t
done << 'EOF'
EOF

%build
get_version() {
	local define="$1" filename="$2"
	awk -vdefine="$define" '/#define/ && $2 == define {print $3}' "$filename" | xargs
}

ver=$(get_version PHP_WDDX_VERSION php_wddx.h)
if test "$ver" != "%{version}-dev"; then
	: Error: Upstream version is now ${ver}, expecting %{version}.
	exit 1
fi

phpize
%configure
%{__make}

# simple module load test
%{__php} -n -q \
	-d extension_dir=modules \
	-d extension=%{php_extensiondir}/xml.so \
	-d extension=%{modname}.so \
	-m > modules.log
grep %{modname} modules.log

%if %{with tests}
./run-tests.sh --show-diff
%endif

%install
rm -rf $RPM_BUILD_ROOT
install -d $RPM_BUILD_ROOT%{php_sysconfdir}/conf.d
install -d $RPM_BUILD_ROOT{%{php_sysconfdir}/conf.d,%{php_extensiondir}}

%{__make} install \
	EXTENSION_DIR=%{php_extensiondir} \
	INSTALL_ROOT=$RPM_BUILD_ROOT

install -d $RPM_BUILD_ROOT%{php_sysconfdir}/conf.d
cat <<'EOF' > $RPM_BUILD_ROOT%{php_sysconfdir}/conf.d/%{modname}.ini
; Enable %{modname} extension module
extension=%{modname}.so
EOF

%clean
rm -rf $RPM_BUILD_ROOT

%post
%php_webserver_restart

%postun
if [ "$1" = 0 ]; then
	%php_webserver_restart
fi

%files
%defattr(644,root,root,755)
%doc CREDITS
%config(noreplace) %verify(not md5 mtime size) %{php_sysconfdir}/conf.d/%{modname}.ini
%attr(755,root,root) %{php_extensiondir}/%{modname}.so
