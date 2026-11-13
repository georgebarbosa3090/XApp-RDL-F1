/* Autor: George Barbosa — relógio simulado do libe42_shim (docs/16, E2). */
#ifndef RDL_SIMCLOCK_H
#define RDL_SIMCLOCK_H

void simclock_register_app_thread(void);
void simclock_advance(double t_s);
void simclock_wait_idle(void);
void simclock_shutdown(void);
double simclock_now(void);

#endif
