#ifndef CATCH_CTRL_C_H
#define CATCH_CTRL_C_H



// abstracting this becauses it differs in Windows and Linux.


bool CtrlC_handler_hook(void (*handleFunc)(void*),void *context);
void CtrlC_handler_unhook();


#endif
