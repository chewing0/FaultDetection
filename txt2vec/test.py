# from text2vec import Anomaly_Detection, vec_save, csv_reader, vec_similar, similar_matrix
import text2vec as t2v

import time
import numpy as np

start_time = time.time()

# Anomaly_Detection()

# t2v.vec_save()

vectors, errs = t2v.csv_reader()
log_vec = t2v.get_logvec()
errtype = t2v.error_type(log_vec, vectors, errs)

print('\n'+'='*40)
print(errtype)
print('='*40)

end_time = time.time()

print('\n'+'='*40)
print("耗时: {:.2f}秒".format(end_time - start_time))
print('='*40)