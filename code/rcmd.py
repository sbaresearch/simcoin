import config


def create_report():
    cp_report_rmd_cmd = 'cp reporter/report.Rmd {}'.format(config.sim_dir)
    change_dir = 'cd {}'.format(config.sim_dir)
    create_report_cmd = r'R -e library\(rmarkdown\)\;rmarkdown::render\(\"report.Rmd\",\"pdf_document\"\)\;q\(\)'
    delete_report_rmd = 'rm report.Rmd'
    return ';'.join([cp_report_rmd_cmd, change_dir, create_report_cmd, delete_report_rmd])