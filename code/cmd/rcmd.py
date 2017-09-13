import config


def create_report(path):
    cp_report_rmd_cmd = 'cp reporter/report.Rmd {}'.format(path)
    change_dir = 'cd {}'.format(path)
    create_report_cmd = r'R -e library\(rmarkdown\)\;rmarkdown::render\(\"report.Rmd\",\"pdf_document\"\)\;q\(\)'
    delete_report_rmd = 'rm report.Rmd'
    return ';'.join([cp_report_rmd_cmd, change_dir, create_report_cmd, delete_report_rmd])
