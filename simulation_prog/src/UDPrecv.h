#ifndef UDP_RECV_H
#define UDP_RECV_H


#define UDP_PORT_LISTEN 12345


bool UDP_setup();
bool UDP_wait(unsigned char *buffer,unsigned int *out_size,int timeout_ms);		// 0 for poll, <0 for infinite . provide 10kiB buffer for jumbo-frames.
void UDP_halt();





#endif
