# Copyright 1999-2004 Gentoo Technologies, Inc.
# Distributed under the terms of the GNU General Public License, v2 or later
# Maintainer: Joonas Kerttula <jokerttu@mail.student.oulu.fi>
# $Header: /home/skyostil/cvsroot/albumart/dist/albumart-1.4.0.ebuild,v 1.1 2004-11-06 17:23:58 skyostil Exp $

S="${WORKDIR}/${P}"

DESCRIPTION="Album Cover Art Downloader"
SRC_URI="http://kempele.fi/~skyostil/projects/albumart/dist/${P}.tar.gz"
HOMEPAGE="http://kempele.fi/~skyostil/projects/albumart/"

LICENSE="GPL-2"
KEYWORDS="x86 sparc ppc alpha hppa mips arm amd64 ia64 ppc64 s390"

DEPEND=">=dev-python/PyQt-3.0
        >=dev-python/Imaging-1.0.0"

src_install() {
	python setup.py install --root= --prefix=/${D}usr || die
}
