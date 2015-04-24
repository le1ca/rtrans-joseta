#include "radio_app.h"
#include <string.h>
#include <stdio.h>

uint16_t app_build_pkt(void *buffer, uint16_t b_len, uint8_t sset_ct, uint8_t samp_ct, char *names[], radio_app_sset *ssets, uint16_t sslen);
uint16_t app_append_sample(void *buf, uint16_t b_len, uint8_t type, void *value);
int8_t   app_get_type_len(uint8_t t);
void     app_decode_pkt(void *buffer, uint16_t len);

int main(int argc, char** argv){
    int i, j;
    char buffer[1024];
    char temp[1024];
    char *names[] = {"one", "two", "three", "four"};
    uint16_t values[] = {0xaaaa, 0xbb, 0xcccc, 0xdd};
   
    void *next = temp;
    uint16_t offset = 0;
    
    uint8_t samp = 4;
    uint8_t sset = 10;
    
    for(i = 0; i < sset; i++){
        for(j = 0; j < samp; j++){
            offset += app_append_sample(next + offset, 1024 - offset, (j%2) ? RA_FMT_u8 : RA_FMT_u16, &values[j]);
        }
    }
    
    
    uint16_t plen = app_build_pkt(buffer, 1024, sset, samp, names, (void *) temp, offset);
    
    printf("packet len is %d bytes\n", plen);
    
    for(i = 0; i < plen; i++)
        printf("%02x ", buffer[i] & 0xff);
    printf("\n\n");
    
    app_decode_pkt(buffer, plen);
    return 0;
}

void app_print_val(radio_app_samp *v){
    switch(v->type){
        case RA_FMT_u64:
            printf("%016llx", v->value.u64);
            break;
        case RA_FMT_u32:
            printf("%08x", v->value.u32);
            break;
        case RA_FMT_u16:
            printf("%04x", v->value.u16);
            break;
        case RA_FMT_u8:
            printf("%02x", v->value.u8);
            break;
        case RA_FMT_i64:
            printf("%lld", v->value.i64);
            break;
        case RA_FMT_i32:
            printf("%d", v->value.i32);
            break;
        case RA_FMT_i16:
            printf("%d", v->value.i16);
            break;
        case RA_FMT_i8:
            printf("%d", v->value.i8);
            break;
        case RA_FMT_f64:
            printf("%f", v->value.f64);
            break;
        case RA_FMT_f32:
            printf("%f", v->value.f32);
            break;
        case RA_FMT_s8:
            printf("%c%c%c%c%c%c%c%c", v->value.s8[0],
                                       v->value.s8[1], 
                                       v->value.s8[2],
                                       v->value.s8[3],
                                       v->value.s8[4],
                                       v->value.s8[5],
                                       v->value.s8[6],
                                       v->value.s8[7]
            );
            break;
        case RA_FMT_s4:
            printf("%c%c%c%c", v->value.s8[0],
                               v->value.s8[1], 
                               v->value.s8[2],
                               v->value.s8[3]
            );
            break;
        case RA_FMT_s2:
            printf("%c%c", v->value.s8[0],
                           v->value.s8[1]
            );
            break;
        default:
            printf("????");
    }
}

void app_decode_pkt(void *buffer, uint16_t len){
    radio_app_pkt *pkt = buffer;
    void *ss = (void*) pkt->name_map + (RA_NAME_LEN * pkt->samp_ct);
    
    int i, j;
    for(i = 0; i < pkt->sset_ct; i++){
        printf("Sample set %02d:\n", i+1);
        for(j = 0; j < pkt->samp_ct; j++){
            printf("  %8s : ", pkt->name_map[j]);
            app_print_val(ss);
            ss += sizeof(uint8_t) + app_get_type_len(((radio_app_samp *) ss)->type);
            printf("\n");
        }
        printf("\n");
    }
}

int8_t app_get_type_len(uint8_t t){

    switch(t){
        
        case RA_FMT_u64:
        case RA_FMT_i64:
        case RA_FMT_f64:
        case RA_FMT_s8:
            return 8;
        
        case RA_FMT_u32:
        case RA_FMT_i32:
        case RA_FMT_f32:
        case RA_FMT_s4:
            return 4;
            
        case RA_FMT_u16:
        case RA_FMT_i16:
        case RA_FMT_s2:
            return 2;
            
        case RA_FMT_u8:
        case RA_FMT_i8:
            return 1;
        
        default:
            return -1;
    }
    
}

uint16_t app_build_pkt(void *buffer, uint16_t b_len, uint8_t sset_ct, uint8_t samp_ct, char *names[], radio_app_sset *ssets, uint16_t sslen){
    int i;
    radio_app_pkt  *p  = buffer;
    radio_app_sset *ss = 0;
    
    // check for sufficient length
    if(b_len < sslen + (2*sizeof(uint8_t)) + (samp_ct*RA_NAME_LEN)){
        return 0;
    }
    
    // set fields
    p->sset_ct = sset_ct;
    p->samp_ct = samp_ct;
    
    // copy names
    for(i = 0; i < p->samp_ct; i++){
        uint8_t len = strlen(names[i]);
        len = (len > RA_NAME_LEN) ? RA_NAME_LEN : len;
        memcpy(p->name_map[i], names[i], len);
    }
    
    // load sample sets
    ss = (void*) buffer + (2*sizeof(uint8_t)) + (samp_ct*RA_NAME_LEN);
    memcpy(ss, ssets, sslen);
    
    // return size
    return sslen + (2*sizeof(uint8_t)) + (samp_ct*RA_NAME_LEN);
}

uint16_t app_append_sample(void *buf, uint16_t b_len, uint8_t type, void *value){
    radio_app_samp *loc = buf;
    int8_t len = app_get_type_len(type);
    
    if(len < 0)
        printf("** invalid type %02x\n", type);
        
    loc->type = type;
    memcpy((void*) &loc->value, value, len);
    
    return sizeof(uint8_t) + len;
}
