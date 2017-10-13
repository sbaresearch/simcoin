import config


def preprocess(path):
    cp_preprocess_r_cmd = 'cp reporter/{} {}'.format(config.preprocess_r_file_name, path)
    change_dir = 'cd {}'.format(path)
    preprocess_cmd = 'Rscript {}'.format(config.preprocess_r_file_name)
    return ';'.join([cp_preprocess_r_cmd, change_dir, preprocess_cmd])


def create_report(path):
    cp_report_rmd_cmd = 'cp reporter/{} {}'.format(config.report_rmd_file_name, path)
    change_dir = 'cd {}'.format(path)
    create_report_cmd = r'R -e library\(rmarkdown\)\;rmarkdown::render\(\"{}\",\"pdf_document\"\)\;q\(\)'\
        .format(config.report_rmd_file_name)
    return ';'.join([cp_report_rmd_cmd, change_dir, create_report_cmd])
