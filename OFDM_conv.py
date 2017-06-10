# Lab 10 MNIST and Dropout
import tensorflow as tf
import random
import numpy as np
import time
from pylab import *
# import matplotlib.pyplot as plt
import shutil
import os


from tensorflow.examples.tutorials.mnist import input_data

#tf.set_random_seed(777)  # reproducibility
tic = time.time()
learning_rate = 0.0001
batch_size = 400
Nsubc = 64
modulation_level = 4
lin_space = np.arange(0,13,2)
for iterN in range(len(lin_space)):
    EbN0dB = lin_space[iterN]
    N0 = 1 / np.log2(modulation_level) / np.power(10.0, EbN0dB / 10.0)
    test_batch_size = 100000
    test_ys = np.random.randint(modulation_level, size=(test_batch_size, Nsubc))
    test_y = np.zeros((test_batch_size, Nsubc * modulation_level))
    for n in range(test_batch_size):
        for m in range(Nsubc):
            test_y[n, m * modulation_level + test_ys[n, m]] = 1
            # test_y[n, 8+np.remainder(n,4)] = 1
    noise_batch_test_r = (np.sqrt(N0 / 2.0)) * np.random.normal(0.0, size=(test_batch_size, Nsubc))
    noise_batch_test_i = (np.sqrt(N0 / 2.0)) * np.random.normal(0.0, size=(test_batch_size, Nsubc))
    # rly = np.random.rayleigh(cha_mag / 2, (test_batch_size, 4))
    rly = np.ones((test_batch_size, Nsubc))
    corruption_r = np.divide(noise_batch_test_r, rly)
    corruption_i = np.divide(noise_batch_test_i, rly)
    corruption_test_batch = corruption_r + 1j * corruption_i

    # test_xs = np.hstack((np.real(message_test), np.imag(message_test))) + (np.random.normal(0, 0.01, (test_batch_size,8)) + 1j*np.random.normal(0, 0.01, (test_batch_size,8)))/np.random.rayleigh(1.0)
    correct_prediction = []
    for i in arange(Nsubc):
        correct_prediction.append(tf.equal(tf.argmax(hypothesis[:, i * modulation_level:(i + 1) * modulation_level], 1), tf.argmax(Y[:, i * modulation_level:(i + 1) * modulation_level], 1)))
    accuracy = tf.reduce_mean(tf.cast(correct_prediction, tf.float32))
    SER = 1 - sess.run(accuracy, feed_dict={X: test_y, Y: test_y, corruption: corruption_test_batch})
    err_rate.append(SER)
np.savetxt("./result/OFDM_SER_trained_at_{0}dB SNR_L4_500000".format(SNR_range), err_rate)

# input place holders
X = tf.placeholder(tf.float32, [None, Nsubc*modulation_level])
Y = tf.placeholder(tf.float32, [None, Nsubc*modulation_level])
corruption = tf.placeholder(tf.complex64,[None, Nsubc])
# peak_power_symbol = tf.placeholder(tf.float32,[batch_size])


# encoded_symbol_normalizing = tf.sqrt(tf.reduce_mean(tf.square(tf.matmul(L4_1, W5_1) + b5_1)))
# encoded_symbol_normalizing = tf.expand_dims(encoded_symbol_normalizing,1) # ,1 is normalizing for every transmit signal i.e. shape (batch_size,1)
# encoded_symbol_original = (1/np.sqrt(2))*tf.div(tf.matmul(L4_1, W5_1) + b5_1, encoded_symbol_normalizing)
raw_symbol = tf.matmul(L4_1, W5_1) + b5_1
even_number = np.arange(0,2*Nsubc,2)
odd_number = np.arange(1,2*Nsubc,2)
X_real = tf.transpose(tf.gather(tf.transpose(raw_symbol),even_number))
X_imag = tf.transpose(tf.gather(tf.transpose(raw_symbol),odd_number))
encoded_symbol_complex = tf.complex(X_real,X_imag)
encoded_symbol_iffted = tf.ifft(encoded_symbol_complex)

# sess = tf.Session()
# sess.run(tf.initialize_all_variables())
# print sess.run(tf.shape(encoded_symbol_iffted))
encoded_symbol_normalizing = tf.reduce_mean(tf.abs(encoded_symbol_iffted))
encoded_symbol_original_r = tf.div(tf.real(encoded_symbol_iffted), encoded_symbol_normalizing)
encoded_symbol_original_i = tf.div(tf.imag(encoded_symbol_iffted), encoded_symbol_normalizing)
encoded_symbol_original = tf.complex(encoded_symbol_original_r, encoded_symbol_original_i)
peak_power_batch = tf.reduce_max(tf.abs(encoded_symbol_original))
avr_power_batch = tf.reduce_mean(tf.abs(encoded_symbol_original))
# for i in np.arange(batch_size):
#     peak_power_symbol[i] = tf.gather_nd(encoded_symbol_original, [i,tf.argmax(tf.abs(encoded_symbol_original[i,:]))]) # kind of tricky
peak_power_symbol = tf.reduce_max(tf.abs(encoded_symbol_original), axis=1)
encoded_symbol = encoded_symbol_original + corruption

received_symbol_complex = tf.fft(encoded_symbol)
received_symbol_r = tf.real(received_symbol_complex)
received_symbol_i = tf.imag(received_symbol_complex)
received_symbol = tf.concat([received_symbol_r, received_symbol_i], axis=1)

W1 = tf.get_variable("W1", shape=[2*Nsubc, 2048], initializer=tf.contrib.layers.xavier_initializer())
b1 = tf.Variable(tf.random_normal([2048]))
L1 = tf.nn.relu(tf.matmul(received_symbol, W1) + b1)
L1 = tf.layers.batch_normalization(L1)

W2 = tf.get_variable("W2", shape=[2048, 2048], initializer=tf.contrib.layers.xavier_initializer())
b2 = tf.Variable(tf.random_normal([2048]))
L2 = tf.nn.relu(tf.matmul(L1, W2) + b2)
L2 = tf.layers.batch_normalization(L2)

W3 = tf.get_variable("W3", shape=[2048, 2048], initializer=tf.contrib.layers.xavier_initializer())
b3 = tf.Variable(tf.random_normal([2048]))
L3 = tf.nn.relu(tf.matmul(L2, W3) + b3)
L3 = tf.layers.batch_normalization(L3)

W4 = tf.get_variable("W4", shape=[2048, 2048], initializer=tf.contrib.layers.xavier_initializer())
b4 = tf.Variable(tf.random_normal([2048]))
L4 = tf.nn.relu(tf.matmul(L3, W4_1) + b4)
L4 = tf.layers.batch_normalization(L4)

W5 = tf.get_variable("W5", shape=[2048, Nsubc*modulation_level], initializer=tf.contrib.layers.xavier_initializer())
b5 = tf.Variable(tf.random_normal([Nsubc*modulation_level]))

hypothesis = tf.matmul(L4, W5) + b5

# define cost/loss & optimizer
#cost = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(logits=hypothesis, labels=Y))
cost = tf.reduce_mean(tf.square(hypothesis-Y)) + 0.01*tf.reduce_mean(peak_power_symbol)
optimizer = tf.train.AdamOptimizer(learning_rate=learning_rate).minimize(cost)
#optimizer = tf.train.RMSPropOptimizer(learning_rate=learning_rate).minimize(cost)

# initialize

sess = tf.Session()
sess.run(tf.global_variables_initializer())
figure()
for SNR_range in np.arange(8,9,2):
    # train my model
    shutil.rmtree('./saved_networks/')
    os.makedirs('./saved_networks/')
    sess = tf.Session()
    sess.run(tf.initialize_all_variables())
    saver = tf.train.Saver()
    checkpoint = tf.train.get_checkpoint_state("saved_networks")
    if checkpoint and checkpoint.model_checkpoint_path:
        saver.restore(sess, checkpoint.model_checkpoint_path)
        print ("Successfully loaded:", checkpoint.model_checkpoint_path)
    else:
        print ("Could not find old network weights")
    lin_space = np.arange(0,13,2)
    print (lin_space)
    cha_mag = 1.0
    err_rate =[]
    for iterN in range(len(lin_space)):

        EbN0dB = lin_space[iterN]
        N0 = 1/np.log2(modulation_level)/1.0*np.power(10.0, -EbN0dB/10.0)
        cost_plot =[]
        if lin_space[iterN] == SNR_range:
            training_epochs = 500000#100+SNR_range*30000
            for epoch in range(training_epochs):
                avg_cost = 0
                batch_ys = np.random.randint(modulation_level, size=(batch_size, Nsubc))
                batch_y = np.zeros((batch_size, Nsubc*modulation_level))
                for n in range(batch_size):
                    for m in range(Nsubc):
                        batch_y[n, m * modulation_level + batch_ys[n, m]] = 1
                noise_batch_r = (np.sqrt(N0 / 2.0)) * np.random.normal(0.0, size=(batch_size, Nsubc))
                noise_batch_i = (np.sqrt(N0 / 2.0)) * np.random.normal(0.0, size=(batch_size, Nsubc))
                #rly = np.random.rayleigh(cha_mag / 2, (batch_size, Nsubc))
                rly = np.ones((batch_size,Nsubc))
                corruption_r = np.divide(noise_batch_r, rly)
                corruption_i = np.divide(noise_batch_i, rly)
                corruption_batch = corruption_r + 1j*corruption_i
                #print (batch_xs.shape)
                #print (batch_ys.shape)
                feed_dict = {X: batch_y, Y: batch_y, corruption: corruption_batch}
                #print 'test1',test1
                # test2 = sess.run(encoded_symbol_normalizing,feed_dict=feed_dict)
                # print 'test2',test2
                # test33 = sess.run(peak_power_symbol, feed_dict=feed_dict)
                # print 'test3', test33
                c, _ = sess.run([cost, optimizer], feed_dict=feed_dict)
                avg_cost += c
                if epoch % 1000 ==0:
                    print('Epoch:', '%04d' % (epoch + 1), 'cost =', '{:.9f}'.format(avg_cost))
                    cost_plot.append(avg_cost)
                    print 'peak_power in transmitted symbol', sess.run(tf.reduce_max(peak_power_symbol), feed_dict=feed_dict), 'avr power', sess.run(avr_power_batch, feed_dict=feed_dict)
                if epoch % 10000 == 0:
                    saver.save(sess, 'saved_networks/' + 'network' + '-OFDM', global_step=epoch)

        print('Learning Finished!')
    # test for SER begin
    for iterN in range(len(lin_space)):
        EbN0dB = lin_space[iterN]
        N0 = 1/np.log2(modulation_level) / np.power(10.0, EbN0dB / 10.0)
        test_batch_size = 100000
        test_ys = np.random.randint(modulation_level, size=(test_batch_size, Nsubc))
        test_y = np.zeros((test_batch_size,Nsubc*modulation_level))
        for n in range(test_batch_size):
            for m in range(Nsubc):
                test_y[n, m * modulation_level + test_ys[n, m]] = 1
                #test_y[n, 8+np.remainder(n,4)] = 1
        noise_batch_test_r = (np.sqrt(N0 / 2.0)) * np.random.normal(0.0, size=(test_batch_size, Nsubc))
        noise_batch_test_i = (np.sqrt(N0 / 2.0)) * np.random.normal(0.0, size=(test_batch_size, Nsubc))
        #rly = np.random.rayleigh(cha_mag / 2, (test_batch_size, 4))
        rly = np.ones((test_batch_size, Nsubc))
        corruption_r = np.divide(noise_batch_test_r, rly)
        corruption_i = np.divide(noise_batch_test_i, rly)
        corruption_test_batch = corruption_r + 1j*corruption_i
        #test_xs = np.hstack((np.real(message_test), np.imag(message_test))) + (np.random.normal(0, 0.01, (test_batch_size,8)) + 1j*np.random.normal(0, 0.01, (test_batch_size,8)))/np.random.rayleigh(1.0)
        correct_prediction=[]
        for i in arange(Nsubc):
            correct_prediction.append(tf.equal(tf.argmax(hypothesis[:, i*modulation_level:(i+1)*modulation_level], 1), tf.argmax(Y[:, i*modulation_level:(i+1)*modulation_level], 1)))
        accuracy = tf.reduce_mean(tf.cast(correct_prediction, tf.float32))
        SER = 1 - sess.run(accuracy, feed_dict={X: test_y, Y: test_y, corruption: corruption_test_batch})
        err_rate.append(SER)
    np.savetxt("./result/OFDM_SER_trained_at_{0}dB SNR_L4_500000".format(SNR_range), err_rate)
    # test for SER end
    # test for CCDF begin
    CCDF = []
    N0 = 1 / np.log2(modulation_level) / np.power(10.0, EbN0dB / 10.0)
    test_batch_size = 100000
    test_ys = np.random.randint(modulation_level, size=(test_batch_size, Nsubc))
    test_y = np.zeros((test_batch_size, Nsubc * modulation_level))
    for n in range(test_batch_size):
        for m in range(Nsubc):
            test_y[n, m * modulation_level + test_ys[n, m]] = 1
            # test_y[n, 8+np.remainder(n,4)] = 1
    noise_batch_test_r = (np.sqrt(N0 / 2.0)) * np.random.normal(0.0, size=(test_batch_size, Nsubc))
    noise_batch_test_i = (np.sqrt(N0 / 2.0)) * np.random.normal(0.0, size=(test_batch_size, Nsubc))
    # rly = np.random.rayleigh(cha_mag / 2, (test_batch_size, 4))
    rly = np.ones((test_batch_size, Nsubc))
    corruption_r = np.divide(noise_batch_test_r, rly)
    corruption_i = np.divide(noise_batch_test_i, rly)
    corruption_test_batch = corruption_r + 1j * corruption_i
    PAPR_sample = sess.run(peak_power_symbol, feed_dict={X: test_y, Y: test_y, corruption: corruption_test_batch})
    print PAPR_sample
    print np.sum(3<10*np.log10(PAPR_sample))
    for z in np.arange(0,6,0.2):
        CCDF.append(np.sum(z<10*np.log10(PAPR_sample))/100000.0)
    np.savetxt("./result/CCDF_trained_at_{0}dB SNR_L4_500000".format(SNR_range), CCDF)
    # test for CCDF end

toc = time.time()
print("elapsed time", toc-tic)
print (lin_space)
print (err_rate)





# Get one and predict
# r = random.randint(0, mnist.test.num_examples - 1)
# print("Label: ", sess.run(tf.argmax(mnist.test.labels[r:r + 1], 1)))
# print("Prediction: ", sess.run(
#     tf.argmax(hypothesis, 1), feed_dict={X: mnist.test.images[r:r + 1], keep_prob: 1}))

# plt.imshow(mnist.test.images[r:r + 1].
#           reshape(28, 28), cmap='Greys', interpolation='nearest')
# plt.show()