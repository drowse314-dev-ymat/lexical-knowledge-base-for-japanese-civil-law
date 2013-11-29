set -e

BUILD_PATH='./jp_civil_law/build'

# Load rdflib graph.
echo "==> Run 'python -m jp_civil_law.run'..."
python -m jp_civil_law.run "$@"
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
