from alive_progress import alive_bar
import torch
import numpy as np
from torch.cuda.amp import GradScaler


def kl_divergence(mu, log_var, beta):
    # mu.shape = (batch_size, latent)
    kl = torch.sum(-0.5 * (1 + log_var - mu ** 2 - torch.exp(log_var)), dim=1)  # (batch_size, 1)
    kl = torch.mean(kl)  # (1)
    return kl * beta


def train(vae, training_data, validation_data, epochs, opt='SGD', beta=1e-5, lr=1e-4, gamma=0.95, device='cuda'):
    print("Commencing training")
    training_losses = np.array([])
    validation_losses = np.array([])
    opt = torch.optim.SGD(vae.parameters(), lr=lr) if opt == 'SGD' else torch.optim.Adam(vae.parameters(), lr=lr)
    scaler = GradScaler()
    # scheduler = torch.optim.lr_scheduler.ExponentialLR(opt, gamma=gamma)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(opt, mode='min', factor=0.5, patience=3)
    MSELoss = torch.nn.MSELoss(reduction='sum')
    for epoch in range(epochs):
        loss_this_epoch = 0
        with alive_bar(total=len(training_data)) as bar:
            for i, x in enumerate(training_data):
                x = x.reshape(x.shape[0], -1)
                x = x.to(device)
                opt.zero_grad()

                with torch.autocast(device_type='cuda', dtype=torch.float16):
                    z, mu, log_var = vae.encoder.forward(x)
                    x_hat = vae.decoder.forward(z)
                    recon_loss = MSELoss(x_hat, x)
                    # kl = torch.mean(-0.5 * (1 + log_var - mu ** 2 - torch.exp(log_var))) * beta
                    kl = kl_divergence(mu, log_var, beta)
                    loss = recon_loss + kl

                scaler.scale(loss).backward()
                scaler.step(opt)
                scaler.update()
                loss_this_epoch += loss  # / len(data)

                bar()

        scheduler.step(loss_this_epoch)
        validation_loss = 0
        for i, x in enumerate(validation_data):
            x = x.to(device)
            with torch.no_grad():
                z, mu, log_var = vae.encoder.forward(x)
                x_hat = vae.decoder.forward(z)
                recon_loss = MSELoss(x_hat, x)
                kl = kl_divergence(mu, log_var, beta)
                validation_loss += recon_loss + kl

        print(f"Epoch: {epoch + 1} out of {epochs}. Training Loss = {loss_this_epoch.item() / len(training_data)}. "
              f"Validation Loss = {validation_loss.item() / len(validation_data)}")
        validation_losses = np.append(validation_losses, float(validation_loss.cpu().detach()))
        training_losses = np.append(training_losses, float(loss_this_epoch.cpu().detach()))
    training_losses /= len(training_data)
    validation_losses /= len(validation_data)
    print(f"Finished Training! Train = {training_losses}. Validation = {validation_losses}")
    return vae, training_losses, validation_losses


def convVAE_train(cvae, training_data, validation_data, epochs, opt='SGD', beta=1e-5, lr=1e-4, device='cuda'):
    training_losses = np.array([])
    validation_losses = np.array([])
    opt = torch.optim.SGD(cvae.parameters(), lr=lr) if opt == 'SGD' else torch.optim.Adam(cvae.parameters(), lr=lr)
    scaler = GradScaler()
    # scheduler = torch.optim.lr_scheduler.ExponentialLR(opt, gamma=gamma)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(opt, mode='min', factor=0.5, patience=3)
    MSELoss = torch.nn.MSELoss(reduction='mean')
    for epoch in range(epochs):
        loss_this_epoch = 0
        with alive_bar(total=len(training_data)) as bar:
            for i, x in enumerate(training_data):
                x = x.to(device)
                x = x.view(x.shape[0], 1, x.shape[1], x.shape[2])
                opt.zero_grad()

                with torch.autocast(device_type='cuda', dtype=torch.float16):
                    z, mu, log_var = cvae.encoder.forward(x)
                    x_hat = cvae.decoder.forward(z).view(x.shape[0], 1, x.shape[2], x.shape[3])
                    recon_loss = MSELoss(x_hat, x)
                    # kl = torch.mean(-0.5 * (1 + log_var - mu ** 2 - torch.exp(log_var))) * beta
                    kl = kl_divergence(mu, log_var, beta)
                    loss = recon_loss + kl

                scaler.scale(loss).backward()
                scaler.step(opt)
                scaler.update()
                loss_this_epoch += loss  # / len(data)

                bar()

        scheduler.step(loss_this_epoch)
        validation_loss = 0
        for i, x in enumerate(validation_data):
            x = x.to(device)
            with torch.no_grad():
                z, mu, log_var = cvae.encoder.forward(x)
                x_hat = cvae.decoder.forward(z)
                recon_loss = MSELoss(x_hat.view(x.shape[0], 1, x.shape[1], -1), x.view(x.shape[0], 1, x.shape[1], -1))
                kl = kl_divergence(mu, log_var, beta)
                validation_loss += recon_loss + kl

        print(f"Epoch: {epoch + 1} out of {epochs}. Training Loss = {loss_this_epoch.item() / len(training_data)}. "
              f"Validation Loss = {validation_loss.item() / len(validation_data)}")
        validation_losses = np.append(validation_losses, float(validation_loss.cpu().detach()))
        training_losses = np.append(training_losses, float(loss_this_epoch.cpu().detach()))
    training_losses /= len(training_data)
    validation_losses /= len(validation_data)
    print(f"Finished Training! Train = {training_losses}. Validation = {validation_losses}")
    return cvae, training_losses, validation_losses
