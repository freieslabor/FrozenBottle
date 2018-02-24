#ifndef FIX_VALUES_H
#define FIX_VALUES_H

#ifdef __cplusplus
extern "C" {
#endif


extern const char fix_map_GBswap[];
extern const char fix_map_4types[];
extern unsigned int fix_map_GBswap__size;

#define NUM_GAMMA_CURVES 4
extern const unsigned char gamma195[];
extern char gamma4[NUM_GAMMA_CURVES][256];



unsigned char chr_2_gammano(char sym);
void load_default_gammacurves();
void correct_values(unsigned char *buffer,unsigned int numleds);
void limit_power(unsigned char *vals,unsigned int num_leds,unsigned char avg_max_pwm);

#ifdef __cplusplus
}
#endif

#endif
