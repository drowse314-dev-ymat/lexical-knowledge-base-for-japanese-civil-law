set -e

BUILD_PATH='./jp_civil_law/build'

# Prune solo nodes in view?
CUT_SOLOS=""
while getopts "c" flag; do
  case $flag in
    c) CUT_SOLOS=" --cut_solos";;
  esac
done

# Load rdflib graph.
echo "==> Run 'python -m jp_civil_law.run'..."
python -m jp_civil_law.run $CUT_SOLOS
echo "==> Finished."
echo ""

# Generate graph as PNG.
echo "==> Generate ${BUILD_PATH}/graph.png..."
dot -Tpdf "${BUILD_PATH}/graph.dot" > "${BUILD_PATH}/graph.pdf"
echo "==> Done."

# Post process. For re-rendering graph, etc.
POSTPROC='postbuild.sh'
if [ -f $POSTPROC ]; then
    sh $POSTPROC
fi
