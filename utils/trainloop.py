from tqdm import tqdm
from utils.loss import MSE_KLD
from torch_geometric.data.batch import Batch
from torch.utils.tensorboard import SummaryWriter


class Trainer():
    def __init__(self, train_config):
        self.model = train_config.model
        self.optimizer = train_config.optimizer
        self.train_loader = train_config.train_loader
        self.device = train_config.device
        self.nn_cfg = train_config.nn_cfg
        self.writer = SummaryWriter("logs")

    def train(self, num_epochs: int) -> None:
        self.model.train()
        for epoch in range(num_epochs):
            self.__epoch(epoch)

    def __epoch(self, epoch: int) -> None:
        with tqdm(self.train_loader, unit="batch") as tepoch:
            for data in tepoch:
                tepoch.set_description(f"Epoch {epoch + 1}")
                original, recon_x, loss = self.__trainloop(data)
                tepoch.set_postfix(loss=loss)

            if (epoch + 1) % 4 == 0:
                self.writer.add_mesh(
                    "original", original[2, :, :].unsqueeze(0).detach(), global_step=epoch)
                self.writer.add_mesh(
                    "point_cloud", recon_x[2, :, :].unsqueeze(0).detach(), global_step=epoch)

    def __trainloop(self, data: Batch):
        self.optimizer.zero_grad()
        pos_reshaped = data.pos.reshape(-1,
                                        self.nn_cfg.num_points, 3).to(self.device)
        # forward pass through the model
        recon_x, mu, log_var = self.model(pos_reshaped.transpose(1, 2))
        # compute the loss
        loss = MSE_KLD(
            recon_x, pos_reshaped, mu, log_var)
        loss.backward()  # compute the gradients
        self.optimizer.step()  # update the parameters
        return pos_reshaped, recon_x, loss.item()

    def release(self):
        self.writer.close()