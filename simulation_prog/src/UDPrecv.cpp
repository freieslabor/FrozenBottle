#include "UDPrecv.h"
#ifdef WIN32
#include <winsock.h>
#else
#include <unistd.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#define  INVALID_SOCKET 0
typedef int SOCKET;
typedef struct timeval TIMEVAL;
#endif
#include <string.h>
#include <stdio.h>


static SOCKET l_sck=INVALID_SOCKET;
#ifdef WIN32
static WSADATA wdat;
#endif

bool UDP_setup()
{
  struct sockaddr_in addr;

#ifdef WIN32
	memset( &wdat , 0 , sizeof(wdat) );
	if(WSAStartup( 0x0101 , &wdat ))
		return false;
#endif

	// create UDP socket
	l_sck = socket(AF_INET,SOCK_DGRAM,IPPROTO_UDP);
#ifdef WIN32
	if( l_sck == INVALID_SOCKET )
#else
	if( l_sck < 0 )
#endif
	{
		UDP_halt();
		return false;
	}

	// set options ( have none )
//	setsockopt( l_sck , SOL_SOCKET , SO_RCVTIMEO , const void *optval , socklen_t optlen );

	// bind to port
	memset( &addr , 0 , sizeof(addr) );
	addr.sin_family = AF_INET;
	addr.sin_addr.s_addr = 0;
	addr.sin_port = htons(UDP_PORT_LISTEN);
	if( bind( l_sck , (const sockaddr*)(&addr) , sizeof(addr) ) < 0 )
	{
		UDP_halt();
		return false;
	}

	printf("listening on UDP port %u\n",(unsigned int)UDP_PORT_LISTEN);

	return true;
}

bool UDP_wait(unsigned char *buffer,unsigned int *out_size,int timeout_ms)
{
  fd_set r_set;
  TIMEVAL tv;
  int res;
#ifdef WIN32
  int nfds = 1;
	r_set.fd_count = 1;
	r_set.fd_array[0] = l_sck;
#else
  int nfds = l_sck+1;
	FD_ZERO(&r_set);
	FD_SET(l_sck,&r_set);
#endif

	if(timeout_ms>0)
	{
		tv.tv_usec = ( timeout_ms % 1000 )*1000 ;
		tv.tv_sec = (timeout_ms/1000);
	}

	res = select( nfds , &r_set , 0 , 0 , (timeout_ms<0?0:&tv) );

	if(res<0)return false;	// I/O error

	if(res==0)return false;	// timeout

	// is ready. do a recv-call.
	res = recv( l_sck , (char*)buffer , 10240 , 0 );

	if( res<=0 )
		return false;	// error

	*out_size = res;

	return true;
}

void UDP_halt()
{
	if( l_sck != INVALID_SOCKET )
	{
		shutdown( l_sck , 0 );
#ifdef WIN32
		closesocket( l_sck );
#else
		close( l_sck );
#endif
		l_sck = INVALID_SOCKET ;
	}

}


