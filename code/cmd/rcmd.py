PREPROCESS_R_FILE = 'preprocess.R'


def preprocess(path):
    cp_preprocess_r_cmd = 'cp reporter/{} {}'.format(PREPROCESS_R_FILE, path)
    change_dir = 'cd {}'.format(path)
    preprocess_cmd = 'Rscript {}'.format(PREPROCESS_R_FILE)
    return ';'.join([cp_preprocess_r_cmd, change_dir, preprocess_cmd])


def create_report(path, file_name):
    cp_report_rmd_cmd = 'cp reporter/{} {}'.format(file_name, path)
    change_dir = 'cd {}'.format(path)
    create_report_cmd = r'R -e library\(rmarkdown\)\;rmarkdown::render\(\"{}\",\"pdf_document\"\)\;q\(\)'\
        .format(file_name)
    return ';'.join([cp_report_rmd_cmd, change_dir, create_report_cmd])
