#!/bin/sh
LANGUAGES="en es_ES ca_ES"
GETTEXT_SCRIPT="pygettext.py"
MSGFMT_SCRIPT="msgfmt.py"
OUTDIR="locales"
DOMAIN="kmixtest"
SEARCH_TRANSLATABLE_FILES_PATH="."

PYVERSION="$(python -c "import sys; print(str(sys.version_info.major)+'.'+str(sys.version_info.minor))" )"
XGETTEXT="$(find /usr/ -name "${GETTEXT_SCRIPT}" 2> /dev/null |grep ${PYVERSION})"
MSGFMT="$(find /usr/ -name "${MSGFMT_SCRIPT}" 2> /dev/null |grep ${PYVERSION})"
MSGMERGE="$(which msgmerge)"

TRANSLATABLE_FILES="$(find "${SEARCH_TRANSLATABLE_FILES_PATH}" -type f | while read in; do if file -i "${in}" |grep -q x-python; then echo "${in}"; fi; done; )"
POTFILE="./${OUTDIR}/${DOMAIN}.pot"

echo Python version: ${PYVERSION}
echo Xgettext script: ${XGETTEXT}
echo Translating files: 
for x in ${TRANSLATABLE_FILES}; do
    echo -e "\t${x}"
done;
echo

$XGETTEXT -d $DOMAIN -o ${POTFILE} ${TRANSLATABLE_FILES}

echo ${POTFILE} generated!

for lang in $LANGUAGES; do
    copydir="${OUTDIR}/${lang}/LC_MESSAGES"
    pofile="${copydir}/${DOMAIN}.po"
    mofile="${copydir}/${DOMAIN}.mo"
    mkdir -p ${copydir}
    if [ -f "${pofile}" ]; then
	${MSGMERGE} -v -U ${pofile} ${POTFILE}
    else
        cp ${POTFILE} ${pofile}
    fi
    ${MSGFMT} -o ${mofile} ${pofile}
done