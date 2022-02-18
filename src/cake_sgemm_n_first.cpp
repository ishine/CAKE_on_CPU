#include "cake.h"


void schedule_NKM(float* A_p, float* B_p, float* C_p, int M, int N, int K, int p, 
	cake_cntx_t* cake_cntx, blk_dims_t* x) {

	// copy over block dims to local vars to avoid readibility ussiues with x->
	int m_r = cake_cntx->mr, n_r = cake_cntx->nr;

	int m_c = (int) cake_cntx->alpha_n*x->m_c, k_c = x->k_c, n_c = x->n_c;
	int m_c1 = x->m_c1, k_c1 = x->k_c1, n_c1 = x->n_c1;
	int k_c1_last_core = x->k_c1_last_core;
	int k_rem = x->k_rem;
	int p_l = x->p_l, m_pad = x->m_pad, k_pad = x->k_pad, n_pad = x->n_pad;
	int Mb = x->Mb, Kb = x->Kb, Nb = x->Nb;
	int N_padded = x->N_padded;

	int m, k, n, n_start, n_end, n_inc, k_start, k_end, k_inc;
	int k_cb, n_c_t, m_c_t, p_used, core;

	// Set the scalars to use during each GEMM kernel call.
	float alpha_blis = 1.0;
	float beta_blis  = 1.0;
    // rsc = 1; csc = m_r;
#ifdef USE_BLIS 
	inc_t rsc, csc;
	rsc = n_r; csc = 1;
	auxinfo_t def_data;
#endif
    // rsa = 1; csa = m_r;
    // rsb = n_r; csb = 1;

	//rsc = 1; csc = m;
	//rsa = 1; csa = m;
	//rsb = 1; csb = k;

	// void (*blis_kernel)(dim_t, float*, float*, float*, 
	// 					float*, float*, inc_t, inc_t, 
	// 					auxinfo_t*, cntx_t*);
	// bli_sgemm_ukernel = bli_sgemm_haswell_asm_6x16;

	for(m = 0; m < Mb; m++) {

		if(m % 2) {
			k_start = Kb - 1;
			k_end = -1;
			k_inc = -1;
		} else {
			k_start = 0;
			k_end = Kb;
			k_inc = 1;
		}

		m_c_t = p*m_c;
		if((m == Mb - 1) && m_pad) {
			m_c_t = m_c1;
		}

		for(k = k_start; k != k_end; k += k_inc) {

			if(m % 2) {
				if(k % 2) {
					n_start = 0;
					n_end = Nb;
					n_inc = 1;
				} else {
					n_start = Nb - 1;
					n_end = -1;
					n_inc = -1;
				}
			} else {
				if(k % 2) {
					n_start = Nb - 1;
					n_end = -1;
					n_inc = -1;
				} else {
					n_start = 0;
					n_end = Nb;
					n_inc = 1;
				}
			}

			if((k == Kb - 1) && k_pad) {
				p_used = p_l;
				k_cb = k_rem; 
			} else {
				p_used = p;
				k_cb = p_used*k_c;
			}

			#pragma omp parallel for private(n, n_c_t, core)
			for(int n_ind = 0; n_ind < Nb; n_ind++) {
			// for(n = 0; n < Nb; n++) {

				n = n_start + n_ind*n_inc;
				
				n_c_t = n_c; 
				if((n == Nb - 1) && n_pad) {
					n_c_t = n_c1;
				}

				// #pragma omp parallel for private(core)
				for(core = 0; core < p_used; core++) {

					// These vars must be private to thread, 
					// otherwise out of bounds memory access possible
					int k_c_t, k_c_x, n_reg, m_reg;

					if((k == Kb - 1) && k_pad) {
						k_c_t = (core == (p_l - 1) ? k_c1_last_core : k_c1);
						k_c_x = k_c1;
					} else {
						k_c_t = k_c;
						k_c_x = k_c;
					}

					int a_ind = m*p*m_c*K + m_c_t*k*p*k_c + core*m_c_t*k_c_x;
					int b_ind = k*p*k_c*N_padded + n*n_c*k_cb + core*k_c_x*n_c_t;
					int c_ind = m*p*m_c*N_padded + m_c_t*n*n_c;

					for(n_reg = 0; n_reg < (n_c_t / n_r); n_reg++) {
						for(m_reg = 0; m_reg < (m_c_t / m_r); m_reg++) {	
												
#ifdef USE_BLIS 
							bli_sgemm_haswell_asm_6x16(k_c_t, &alpha_blis, 
					   		&A_p[a_ind + m_reg*m_r*k_c_t], 
					   		&B_p[b_ind + n_reg*k_c_t*n_r], &beta_blis, 
					   		&C_p[c_ind + n_reg*m_c_t*n_r + m_reg*m_r*n_r], 
					   		rsc, csc, &def_data, cake_cntx->blis_cntx);

#elif USE_CAKE
							cake_sgemm_haswell_6x16(&A_p[a_ind + m_reg*m_r*k_c_t], 
													&B_p[b_ind + n_reg*k_c_t*n_r], 
													&C_p[c_ind + n_reg*m_c_t*n_r + m_reg*m_r*n_r], 
													m_r, n_r, k_c_t);
#endif

						}
					}
				}
			}
		}
	}
}


