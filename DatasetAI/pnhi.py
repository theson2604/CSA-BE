stats_df = []
beta_stats_df = []

save_csv_path = '../notebook-test/result'  # khai đường dẫn cho kết quả
save_plot_path = '../notebook-test/result'   # khai đường dẫn cho đồ thị

for ticker in tickers:  # chạy tuần tự từng mã (một công việc cho nhiều mã)
    in_samples = df_log_ret.loc[:'2015', ticker]  # chia đôi dữ liệu, từ 2001-2015 (in sample), và 2016 đến hiện tại (out of sample)
    out_samples = df_log_ret.loc['2016':, ticker]
    
    for q in quantiles:
        # --------- model o day ------------
        caviar_model = CaviarModel(quantile=q, model=model, method='RQ')  # đổi ở đây nè
        caviar_model.fit(in_samples)  # hàm nằm trong file CaViaR/caviar/caviar_model.py
        
        # save plots
        fig1 = caviar_model.plot_caviar(in_samples, 'in')
        plt.savefig(f'{save_plot_path}/{model}_{int(q*100)}%_plt_caviar_in.jpg')
        fig2 = caviar_model.plot_caviar(out_samples, 'out')
        plt.savefig(f'{save_plot_path}/{model}_{int(q*100)}%_plt_caviar_out.jpg')
        fig3 = caviar_model.plot_news_impact_curve()
        plt.savefig(f'{save_plot_path}/{model}_{int(q*100)}%_plt_news_impact_curve.jpg')
                    
        # as the last prediction is the VaR forecast
        in_VaR = caviar_model.predict(in_samples, 'in')[:-1]
        out_VaR = caviar_model.predict(out_samples, 'out')[:-1]

        # statistics
        stat = {
            'quantile': q,
            'model': model,
            'method': 'RQ',  # có thể thay thế bằng phương pháp MLE, đổi ở phía trên
            # 'trial': i,
            
            # insamples
            'loss': caviar_model.training_loss,  
            'hit_rate_in': hit_rate(in_samples, in_VaR),
            'binom_in': binomial_test(in_samples, in_VaR, q),
            'traffic_in': traffic_light_test(in_samples, in_VaR, q)[0],
            'kupiec_in': kupiec_pof_test(in_samples, in_VaR, q),
            'independent_in': christoffersen_test(in_samples, in_VaR),
            'dq_in': caviar_model.dq_test(in_samples, 'in'),
            # outsamples
            'hit_rate_out': hit_rate(out_samples, out_VaR),
            'binom_out': binomial_test(out_samples, out_VaR, q),
            'traffic_out': traffic_light_test(out_samples, out_VaR, q)[0],
            'kupiec_out': kupiec_pof_test(out_samples, out_VaR, q),
            'independent_out': christoffersen_test(out_samples, out_VaR),
            'dq_out': caviar_model.dq_test(in_samples, 'in'),                
        }

        beta_stat = caviar_model.beta_summary() 
        beta_stat['quantile'] = q
        beta_stat['model'] = model
        beta_stat['method'] = 'RQ'
        # beta_stat['trial'] = i

        stats_df.append(stat)
        beta_stats_df.append(beta_stat)