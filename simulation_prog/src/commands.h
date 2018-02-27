#ifndef COMMANDS_H


// component for processing 'commands' to the LED server.
// A packet is treated as a command and not a bunch of RGB values,
// if it starts with the 16-byte sequence COMMAND_PCK_PREFIX.
// then the reset of it (after the 16 byte head) is passed to
// process_command_packet().
//



#define COMMAND_PCK_PREFIX "COMMAND_2_SERVER"   // 16 byte prefix string. keep length at 16.


#ifdef __cplusplus
extern "C" {
#endif

int process_command_packet(const char *cmd);
int process_command_packet_gamma(const char *cmd);

#ifdef __cplusplus
}
#endif

#endif
