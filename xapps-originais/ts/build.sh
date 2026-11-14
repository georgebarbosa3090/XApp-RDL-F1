#!/usr/bin/env bash
# Autor: George Barbosa
# Compila o Traffic Steering original (o-ran-sc/ric-app-ts, sem alteração) e as dependências do O-RAN SC
# (RMR e xapp-frame-cpp) num prefixo local, sem sudo (docs/16, etapa E3). Confere o sha256 do ts_xapp.cpp
# contra third_party/xapps/ric-app-ts/SOURCE.md. Uso (Ubuntu do WSL): bash xapps-originais/ts/build.sh
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
SRCS="${XAPPS_ORIGINAIS:-$HOME/xapps-originais}"
P="${TS_PREFIX:-$SRCS/install}"
J="${JOBS:-1}"
mkdir -p "$P"
want=$(grep -F '`src/ts_xapp/ts_xapp.cpp`' "$REPO/third_party/xapps/ric-app-ts/SOURCE.md" | grep -oE '[0-9a-f]{64}')
got=$(sha256sum "$SRCS/ric-app-ts/src/ts_xapp/ts_xapp.cpp" | cut -d' ' -f1)
[ "$want" = "$got" ] || { echo "sha256 diverge: ts_xapp.cpp" >&2; exit 65; }
echo "ts_xapp.cpp conferido (sha256 do SOURCE.md)"
export CPATH="$P/include:${CPATH:-}" LIBRARY_PATH="$P/lib:${LIBRARY_PATH:-}" LD_LIBRARY_PATH="$P/lib:${LD_LIBRARY_PATH:-}"

build() {  # nome origem args...
  local name="$1" src="$2"; shift 2
  echo "=== $name"
  cmake -S "$src" -B "$SRCS/build-$name" -DCMAKE_INSTALL_PREFIX="$P" -DCMAKE_PREFIX_PATH="$P" "$@" > "$SRCS/build-$name.cmake.log" 2>&1 \
    || { tail -25 "$SRCS/build-$name.cmake.log"; exit 1; }
  nice -n 19 cmake --build "$SRCS/build-$name" -j"$J" > "$SRCS/build-$name.make.log" 2>&1 \
    || { grep -E "error|Error" "$SRCS/build-$name.make.log" | head -20; exit 1; }
  cmake --install "$SRCS/build-$name" > /dev/null 2>&1 || true
  echo "ok $name"
}
[ -f "$P/lib/librmr_si.a" ] || build rmr "$SRCS/ric-plt-lib-rmr" -DDEV_PKG=1
# DEV_PKG=1 instala só a .a e os cabeçalhos; o adaptador (scripts/closed_loop/ts_driver.py) carrega a .so
cp -P "$SRCS"/build-rmr/librmr_si.so* "$P/lib/" 2>/dev/null || true
# xapp-frame-cpp: só o núcleo que o TS usa (messaging, json, alarm, metrics, config, xapp). Os módulos
# rest-client (cpprest) e rest-server (Pistache) não são usados pelo TS, que tem o próprio cliente REST com
# curl (src/utils/restclient), e exigiriam dependências fora do apt já instalado. Mesma abordagem do shim do
# FlexRIC: alvos de objeto e regras de instalação originais, sem alterar fonte.
xfcpp_core() {
  local X="$SRCS/ric-plt-xapp-frame-cpp" B="$SRCS/build-xfcpp" d
  local parts="messaging json alarm metrics config xapp"
  echo "=== xfcpp (núcleo)"
  cmake -S "$X" -B "$B" -DCMAKE_INSTALL_PREFIX="$P" -DCMAKE_PREFIX_PATH="$P" -DDEV_PKG=1 > "$B.cmake.log" 2>&1 \
    || { tail -25 "$B.cmake.log"; exit 1; }
  nice -n 19 cmake --build "$B" -j"$J" --target message_objects json_objects alarm_objects metrics_objects \
    config_objects xapp_objects > "$B.make.log" 2>&1 || { grep -E "error|Error" "$B.make.log" | head -20; exit 1; }
  rm -f "$P/lib/libricxfcpp.a"
  for d in $parts; do find "$B/src/$d" -name '*.o' -print0 | xargs -0 ar rcs "$P/lib/libricxfcpp.a"; done
  for d in $parts; do cmake -P "$B/src/$d/cmake_install.cmake" > /dev/null; done
  echo "ok xfcpp (núcleo)"
}
[ -f "$P/lib/libricxfcpp.a" ] || xfcpp_core
# O ric-app-ts traz rc.pb.* e rc.grpc.pb.* gerados por um protoc antigo, incompatível com o protobuf do
# Ubuntu (3.21). Numa cópia de build, regenera só esse código gerado a partir do rc.proto original; os fontes
# do TS ficam intactos (o sha256 do ts_xapp.cpp é conferido também na cópia).
TSRC="$SRCS/ric-app-ts-build-src"
rm -rf "$TSRC" && cp -r "$SRCS/ric-app-ts" "$TSRC" && rm -rf "$TSRC/.git"
[ "$(sha256sum "$TSRC/src/ts_xapp/ts_xapp.cpp" | cut -d' ' -f1)" = "$want" ] || { echo "sha256 diverge na cópia" >&2; exit 65; }
( cd "$TSRC/ext/protobuf" && rm -f rc.pb.* rc.grpc.pb.* \
  && protoc -I. --cpp_out=. --grpc_out=. --plugin=protoc-gen-grpc="$(command -v grpc_cpp_plugin)" rc.proto ) \
  || { echo "falha ao regenerar o código do rc.proto" >&2; exit 1; }
echo "rc.proto regenerado com $(protoc --version)"
rm -rf "$SRCS/build-ts"
# o gRPC do Ubuntu separa a libgpr; o CMake do TS só lista grpc++, então o ligador resolve as dependências
# transitivas das .so (sem mudar o CMakeLists original)
build ts "$TSRC" -DCMAKE_EXE_LINKER_FLAGS="-Wl,--copy-dt-needed-entries"
ls -la "$SRCS/build-ts/src/ts_xapp/ts_xapp" 2>/dev/null || find "$SRCS/build-ts" -name ts_xapp -type f
