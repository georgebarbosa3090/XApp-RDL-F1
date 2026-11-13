# Autor: George Barbosa
# libe42_shim (backend ns-3) e as xApps originais do FlexRIC ligadas a ele (docs/16, E2).
# As fontes das xApps são as originais, sem alteração (sha256 conferido por build.sh contra
# third_party/xapps/*/SOURCE.md). Elas incluem cabeçalhos por caminho relativo
# ("../../../../src/..."), por isso são copiadas para <FLEXRIC_DIR>/examples/xApp/c/rdl/.
cmake_minimum_required(VERSION 3.16)
project(rdl_e42_shim C)

set(FLEXRIC_DIR "$ENV{HOME}/xapps-originais/flexric-orange" CACHE PATH "árvore FlexRIC (ramo oie-ric-taap-xapps, f56d448)")
set(FLEXRIC_BUILD "${FLEXRIC_DIR}/build" CACHE PATH "build da árvore FlexRIC (bibliotecas das SMs)")
set(XSLICE_SRC "$ENV{HOME}/xapps-originais/xslice-oran/examples/xApp/c/ctrl/xapp_xslice.c" CACHE FILEPATH "xApp xSlice original")
set(ES_SRC "${FLEXRIC_DIR}/examples/xApp/c/orange/xapp_es_with_cell_util.c" CACHE FILEPATH "xApp ES Orange original")

set(CMAKE_C_STANDARD 11)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)
add_compile_definitions(E2AP_V2 KPM_V2_03 _GNU_SOURCE)
add_compile_options(-w)  # avisos do código de terceiros não são nossos

set(SRC "${FLEXRIC_DIR}/src")
# Utilitários: as bibliotecas estáticas das SMs já trazem a maioria; aqui só os que faltam nelas.
set(FR_UTIL "${SRC}/util/conf_file.c" "${SRC}/util/time_now_us.c" "${SRC}/util/alg_ds/alg/defer.c")
# só a representação intermediária (ie/); dec/ e enc/ dependem do código ASN.1 gerado
file(GLOB_RECURSE FR_LIB3GPP CONFIGURE_DEPENDS "${SRC}/lib/3gpp/ie/*.c")
file(GLOB_RECURSE FR_LIBSM CONFIGURE_DEPENDS "${SRC}/lib/sm/ie/*.c")
file(GLOB_RECURSE FR_E2AP_TYPES CONFIGURE_DEPENDS "${SRC}/lib/e2ap/v2_03/e2ap_types/*.c")
set(FR_XAPP_IR "${SRC}/xApp/e2_node_arr_xapp.c" "${SRC}/xApp/e2_node_connected_xapp.c"
               "${SRC}/xApp/sm_ran_function.c" "${SRC}/xApp/sm_ran_function_def.c")

add_library(e42_shim SHARED e42_shim.c simclock.c ${FR_UTIL} ${FR_LIB3GPP} ${FR_LIBSM} ${FR_E2AP_TYPES} ${FR_XAPP_IR})
target_include_directories(e42_shim PUBLIC "${SRC}" "${CMAKE_CURRENT_SOURCE_DIR}")
set(FR_SM_LIBS
  "${FLEXRIC_BUILD}/src/sm/kpm_sm/kpm_sm_v02.03/libkpm_sm_static.a"
  "${FLEXRIC_BUILD}/src/sm/rc_sm/librc_sm_static.a"
  "${FLEXRIC_BUILD}/src/sm/mac_sm/libmac_sm_static.a"
  "${FLEXRIC_BUILD}/src/sm/rlc_sm/librlc_sm_static.a"
  "${FLEXRIC_BUILD}/src/sm/pdcp_sm/libpdcp_sm_static.a"
  "${FLEXRIC_BUILD}/src/sm/gtp_sm/libgtp_sm_static.a"
  "${FLEXRIC_BUILD}/src/sm/slice_sm/libslice_sm_static.a"
  "${FLEXRIC_BUILD}/src/sm/tc_sm/libtc_sm_static.a"
  "${FLEXRIC_BUILD}/src/sm/ccc_sm/libccc_sm_static.a")
# sem --whole-archive: cada .a das SMs traz cópias dos utilitários; o ligador puxa só o que falta
target_link_libraries(e42_shim PRIVATE -Wl,--start-group ${FR_SM_LIBS} -Wl,--end-group pthread m)
target_link_options(e42_shim PRIVATE -Wl,--no-undefined)

set(STAGE "${FLEXRIC_DIR}/examples/xApp/c/rdl")
file(MAKE_DIRECTORY "${STAGE}")
configure_file("${ES_SRC}" "${STAGE}/xapp_es_with_cell_util.c" COPYONLY)
configure_file("${XSLICE_SRC}" "${STAGE}/xapp_xslice.c" COPYONLY)

foreach(x xapp_es_with_cell_util xapp_xslice)
  add_executable(${x}_rdl "${STAGE}/${x}.c")
  target_include_directories(${x}_rdl PRIVATE "${SRC}")
  # o shim vem antes da libc: sleep/usleep/nanosleep/time da xApp resolvem para o relógio simulado
  target_link_libraries(${x}_rdl PRIVATE e42_shim -Wl,--start-group ${FR_SM_LIBS} -Wl,--end-group pthread m)
  set_target_properties(${x}_rdl PROPERTIES BUILD_RPATH "$<TARGET_FILE_DIR:e42_shim>")
endforeach()
