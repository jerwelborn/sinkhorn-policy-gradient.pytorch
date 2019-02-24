#!/bin/bash
N_NODES=10 # what's this?
N_FEATURES=1 # vs this?
COP="sort_0-9"
ACTOR_WORKERS=4
ARCH='sequential'
RANDOM_SEED=$1
RUN_NUM=$2
RUN_NAME="$COP-$N_NODES-$RANDOM_SEED$RUN_NUM"
TRAIN_SIZE=50000 #0
TEST_SIZE=1000
PARALLEL_ENVS=128
BATCH_SIZE=128
ACTOR_LR=1e-5 
CRITIC_LR=2e-4 
ACTOR_LR_DECAY_RATE=0.95
CRITIC_LR_DECAY_RATE=0.95
ACTOR_LR_DECAY_STEP=5000
CRITIC_LR_DECAY_STEP=5000
N_EPOCHS=10
K_EXCHANGE=2
EPSILON=1.
EPSILON_DECAY_RATE=0.95
EPSILON_DECAY_STEP=$TRAIN_SIZE
BUFFER_SIZE=1000000
SINKHORN_TAU=0.05
SINKHORN_ITERS=10
ID=$RANDOM_SEED
DISABLE_TENSORBOARD='True'
EMBEDDING_DIM=128
RNN_DIM=128
USE_CUDA='False'
CUDA_DEVICE=0
REPLAY_BUFFER_GPU='False'
EPOCH_START=0
SAVE_STATS='False'
SAVE_MODEL='False'
BASE_DIR='.'
MAKE_ONLY=3
#ACTOR_LOAD_PATH='results/models/mwm2D/spg/siamese/120/actor-epoch-6.pt'
#CRITIC_LOAD_PATH='results/models/mwm2D/spg/siamese/91212/critic-epoch-100.pt'

python3 train_spg.py --task $COP --arch $ARCH --train_size $TRAIN_SIZE \
                    --test_size $TEST_SIZE --batch_size $BATCH_SIZE --n_nodes $N_NODES \
                    --n_features $N_FEATURES --random_seed $RANDOM_SEED --run_name $RUN_NAME \
                    --disable_tensorboard $DISABLE_TENSORBOARD --actor_lr $ACTOR_LR \
                    --critic_lr $CRITIC_LR --n_epochs $N_EPOCHS --buffer_size $BUFFER_SIZE \
                    --epsilon $EPSILON --epsilon_decay_rate $EPSILON_DECAY_RATE \
                    --epsilon_decay_step $EPSILON_DECAY_STEP --_id $ID \
                    --sinkhorn_iters $SINKHORN_ITERS --sinkhorn_tau $SINKHORN_TAU \
                    --save_stats $SAVE_STATS --embedding_dim $EMBEDDING_DIM --rnn_dim $RNN_DIM \
                    --actor_lr_decay_rate $ACTOR_LR_DECAY_RATE --actor_lr_decay_step $ACTOR_LR_DECAY_STEP \
                    --critic_lr_decay_rate $CRITIC_LR_DECAY_RATE --critic_lr_decay_step $CRITIC_LR_DECAY_STEP \
                    --k_exchange $K_EXCHANGE --use_cuda $USE_CUDA --save_model $SAVE_MODEL \
                    --parallel_envs $PARALLEL_ENVS  --cuda_device $CUDA_DEVICE --base_dir $BASE_DIR \
                    --actor_workers $ACTOR_WORKERS --replay_buffer_gpu $REPLAY_BUFFER_GPU --make_only $MAKE_ONLY