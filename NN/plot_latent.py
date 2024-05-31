from plot import *
# from sklearn.manifold import TSNE

data_dir = '/home/midml/Desktop/Leo_project/Benjolin_MA/param2latent_datasets/latent_dataset_param_vae8.npz'
dataset = np.load(data_dir)
latent = dataset['latent_matrix']
parameter = dataset['parameter_matrix']
print(latent.shape)
print(parameter.shape)

# parameter_tsne = TSNE(n_components=2).fit_transform(parameter)

# plot_correlation(latent, parameter, '01_RUN')
# plt.scatter(latent[:, 0], latent[:, 1], alpha=0.8, s=0.3)
plot_latent(latent, parameter)
plot_correlation(latent, parameter, knob='FIL_FRQ')
