import os
import sys
import utils
import basic_seq2seq
import tensorflow as tf

class Config(object):
    vocab_size = 10000
    embed_dim = encode_embed_dim = decode_embed_dim = 500
    encoder_hidden_units = decoder_hidden_units = 100
    batch_size = 64
    sequence_length = decode_sequence_length = encode_sequence_length = 30
    steps_per_checkpoint = 50
    max_epochs = 15

    data_path = './data/Training_Shuffled_Dataset.txt'
    train_dir = './models/baseline'

config = Config()
vocab = utils.Vocab()
vocab.construct(config.data_path, config.vocab_size)
data_reader = utils.DataReader(vocab)
data_reader.construct(config.data_path, sent_size=config.sequence_length)
config.vocab = vocab
config.data_reader = data_reader

if not os.path.exists(config.train_dir):
    os.makedirs(config.train_dir)

tf.reset_default_graph()
model = basic_seq2seq.LanguageSeq2Seq(config)
sess = tf.InteractiveSession()
sess.run(tf.global_variables_initializer())

loss_track = list()
for epoch in range(model.config.max_epochs):
    batch_iter = model.config.data_reader.get_iterator(model.config.batch_size, meta_tokens=None)
    for batch, encoder_inputs_, decoder_inputs_, decoder_targets_ in batch_iter:
        feed_dict = {model.encoder_inputs: encoder_inputs_.T,
                     model.decoder_inputs: decoder_inputs_.T,
                     model.decoder_targets: decoder_targets_.T}
        _, batch_loss = sess.run([model.train_op, model.loss], feed_dict)
        if batch % model.config.steps_per_checkpoint == 0:
                print('Epoch {}, batch {}'.format(epoch, batch))
                print('  minibatch loss: {}'.format(batch_loss))

                predict_, generate_ = sess.run([model.decoder_prediction, model.generated_preds], feed_dict)  
                for i, (inp, pred, gen) in enumerate(zip(feed_dict[model.encoder_inputs].T, predict_.T, generate_.T)):
                    inp_decode = " ".join([model.config.vocab.decode(x) for x in inp[::-1]])
                    pred_decode = " ".join([model.config.vocab.decode(x) for x in pred])
                    gen_decode = " ".join([model.config.vocab.decode(x) for x in gen])
                    print('  sample {}:'.format(i + 1))
                    print('    input     > {}'.format(inp_decode))
                    print('    fed       > {}'.format(pred_decode))
                    print('    generated > {}'.format(gen_decode))
                    if i >= 5: break
                    print()    
     
                checkpoint_path = os.path.join(model.config.train_dir, "chatbot.ckpt")
                model.saver.save(sess, checkpoint_path) 

    checkpoint_path = os.path.join(model.config.train_dir, 'chatbot_epoch_%d.ckpt'%(epoch + 1))
    model.saver.save(sess, checkpoint_path)



