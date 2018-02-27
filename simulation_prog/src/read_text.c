#include <string.h>
#include "read_text.h"


#define is_letter(a) ( ((a)>='a'&&(a)<='z') || ((a)>='A'&&(a)<='Z') )
#define is_digit(a) ( (a)>='0' && (a)<='9' )
#define is_hex(a) ( ((a)>='0'&&(a)<='9') || ((a)>='a'&&(a)<='f') || ((a)>='A'&&(a)<='F') )

#define hexdigval(a) ( ((a)>='0'&&(a)<='9') ? ((a)-'0') : (((a)-'a')&0xf)+10 )



void skip_whitespace(const char **ptr,char skip_cr)
{
  const char *rd=*ptr;
	while( *rd==' ' || *rd==9 || (skip_cr&&(*rd==13||*rd==10)) )
		rd++;
	*ptr=rd;
}

char to_nextline(const char **ptr)
{
  const char *rd=*ptr;
  char res;
	while( *rd && *rd!=10 )
		rd++;
	res=0;
	if(*rd==10)
	{
		res=1;
		rd++;
	}
	*ptr=rd;
	return res;
}

char read_identifier(const char **ptr,char *buffer,unsigned int buffersize)
{
  const char *rd=*ptr;
  unsigned int t;
	skip_whitespace(&rd,0);
	for(t=0UL;rd[t];t++)
	{
		if( (!is_letter(rd[t])) && (t==0||(!is_digit(rd[t]))) && rd[t]!='_' )
			break;
	}
	if( t<1 || t>=buffersize )
		return 0;
	memcpy(buffer,rd,t);
	buffer[t]=0;
	rd+=t;
	*ptr=rd;
	return 1;
}

char read_int(const char **ptr,int32_t *result)
{
  const char *rd=*ptr;
  int64_t tmp;
	if(!read_int64(&rd,&tmp))
		{return 0;}
	if( tmp<((int32_t)0x80000000) || tmp>0x7FFFFFFF )
		{return 0;}
	*result=(int32_t)tmp;
	*ptr=rd;
	return 1;
}

char read_uint(const char **ptr,uint32_t *result)
{
  const char *rd=*ptr;
  int64_t tmp;
	tmp=read_int64(&rd,&tmp);
	if( tmp<0 || (uint64_t)tmp>0x0FFFFFFFFUL )
		{return 0;}
	*result=(uint32_t)tmp;
	*ptr=rd;
	return 1;
}

char read_int64(const char **ptr,int64_t *result)
{
  const char *rd=*ptr;
  uint64_t val,prevval;
  char have_digits;
  char is_hex,is_neg;
	val=0;
	is_hex=0;
	is_neg=0;
	have_digits=0;
	skip_whitespace(&rd,0);
	if(*rd=='-')
		{is_neg++;rd++;}
	while(*rd=='0')
		{rd++;have_digits=1;}
	if(*rd=='x'||*rd=='X')
		{rd++;have_digits=0;}
	while( (is_hex&&is_hex(*rd)) || ((!is_hex)&&is_digit(*rd)) )
	{
		have_digits=1;
		prevval=val;
		val=(is_hex?16:10)*val+hexdigval(*rd);
		//printf(".......havedig......%d\n",(int)val);
		if(val<prevval)
			{return 0;}
		rd++;
	}
	if(!have_digits)
		{return 0;}
	if(
		( (!is_neg) && val>=0x8000000000000000U )  ||
		( (is_neg) && val>0x8000000000000000U )
	)
		{return 0;}
	*result=(is_neg?-(int64_t)val:val);
	*ptr=rd;
	return 1;
}

char read_double(const char **ptr,double *result)
{
  const char *rd=*ptr;
  int64_t mant;
  int32_t pow,tmp;
  char have_digits;
  char is_neg,comma,Eneg;
  double res,dtmp;
  static const double powfac[9]=
  {
	1.0E01,1.0E02,1.0E04,1.0E08, 1.0E16,1.0E32,1.0E64,1.0E128, 1.0E256
  };
	skip_whitespace(&rd,0);
	is_neg=0;
	pow=0;
	have_digits=0;
	//check sign
	if(*rd=='-')
		{is_neg++;rd++;}
	//get decimal mantissa
	comma=0;
	mant=0;
	while( *rd )
	{
		if(is_digit(*rd))
		{
			have_digits=1;
			if(comma)pow--;
			if(mant<0x07FFFFFFFFFFFFFF)
				{mant=mant*10+(*rd-'0');}
			else
				pow++;
		}else if(*rd=='.')
		{
			if(comma)
				{return 0;}
			comma=1;
		}else
			break;
		rd++;
	}
	if(!have_digits)
		{return 0;}
	if(*rd=='e'||*rd=='E')
	{
		rd++;
		Eneg=0;
		if(*rd=='+')
			rd++;
		else if(*rd=='-')
			{rd++;Eneg=1;}
		if(!read_int(&rd,&tmp))
			return 0;
		pow+=(Eneg?-tmp:tmp);
	}
	//now apply power and return result.
	res=(double)mant;
	dtmp=1.0;
	if(pow>=0)
	{
		if(pow&~0x01FF)
			{return 0;}
		for(tmp=9;tmp>=0;--tmp)
			if(pow&(1<<tmp))
				dtmp*=powfac[tmp];
		res*=dtmp;
	}else{
		pow=-pow;
		for(tmp=9;tmp>=0;--tmp)
			if(pow&(1<<tmp))
				dtmp*=powfac[tmp];
		res/=dtmp;
		if(pow&~0x01FF)
			res=0.0;
	}
	*result=(is_neg?-res:res);
	*ptr=rd;
	return 1;
}

char read_bool(const char **ptr,char *result)
{
  const char *rd=*ptr;
  char bl_tmp[8];
  char res;
  char *sit;
	if( (*rd=='0') || (*rd=='1') )
		{*result=(*rd=='1');rd++;*ptr=rd;return 1;}
	//read word
	if(!read_identifier(&rd,bl_tmp,sizeof(bl_tmp)))
		return 0;
	//to lower
	for(sit=bl_tmp;*sit;++sit)
	{
		if(*sit>='A'&&*sit<='Z')
			*sit=*sit+('a'-'A');
	}
	//check words
	res=0;
	if(!strcmp(bl_tmp,"true"))
		res=1;
	else if(!strcmp(bl_tmp,"false"))
		res=0;
	else if(!strcmp(bl_tmp,"yes"))
		res=1;
	else if(!strcmp(bl_tmp,"no"))
		res=0;
	else if(!strcmp(bl_tmp,"on"))
		res=1;
	else if(!strcmp(bl_tmp,"off"))
		res=0;
	else
		{return 0;}
	*result=res;
	*ptr=rd;
	return res;
}

char read_vector(const char **ptr,unsigned int components,double *result_array)
{
  const char *rd=*ptr;
  double tmp;
	skip_whitespace(&rd,0);
	if(*rd!='(')
		{return 0;}
	rd++;
	while(components>0)
	{
		components--;
		skip_whitespace(&rd,0);
		if(!read_double(&rd,&tmp))
			return 0;
		if(components>0)
		{
			skip_whitespace(&rd,0);
			if( *rd!='/' && *rd!=';' && *rd!=',' )
				{return 0;}
			rd++;
		}
		*(result_array++)=tmp;
	}
	skip_whitespace(&rd,0);
	if(*rd!=')')
		{return 0;}
	rd++;
	*ptr=rd;
	return 1;
}

