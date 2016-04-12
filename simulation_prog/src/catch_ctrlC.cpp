#include "catch_ctrlC.h"

static void *handler_data;
static void (*handler_func)(void *);

#ifdef WIN32

#include <Windows.h>

static BOOL WINAPI _handler(_In_ DWORD CtrlType)
{
	handler_func(handler_data);
	return TRUE;
}

bool CtrlC_handler_hook(void (*handleFunc)(void*),void *context)
{
  BOOL res;
	handler_data = context;
	handler_func = handleFunc;
	res = SetConsoleCtrlHandler(_handler,TRUE);
	return res!=FALSE;
}

void CtrlC_handler_unhook()
{
	SetConsoleCtrlHandler(_handler,FALSE);
}

#else

#include <signal.h>
#include <string.h>

static void _handler(int dummy)
{
	handler_func(handler_data);
}

bool CtrlC_handler_hook(void (*handleFunc)(void*),void *context)
{
  struct sigaction act;
  int res;
	handler_data = context;
	handler_func = handleFunc;
	memset( &act , 0 , sizeof(act) );
	act.sa_handler = _handler;
	res = sigaction(SIGINT,&act,0);
	return res==0;
}

void CtrlC_handler_unhook()
{
  struct sigaction act;
	memset( &act , 0 , sizeof(act) );
	act.sa_handler = SIG_DFL;
	sigaction(SIGINT,&act,0);
}

#endif
