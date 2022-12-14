-- MySQL Script generated by MySQL Workbench
-- Wed Dec 14 16:12:52 2022
-- Model: New Model    Version: 1.0
-- MySQL Workbench Forward Engineering

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

-- -----------------------------------------------------
-- Schema mydb
-- -----------------------------------------------------

-- -----------------------------------------------------
-- Schema mydb
-- -----------------------------------------------------
CREATE SCHEMA IF NOT EXISTS `mydb` DEFAULT CHARACTER SET utf8 ;
USE `mydb` ;

-- -----------------------------------------------------
-- Table `mydb`.`Subjects`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `mydb`.`Subjects` ;

CREATE TABLE IF NOT EXISTS `mydb`.`Subjects` (
  `subject_id` INT NOT NULL AUTO_INCREMENT,
  `title` VARCHAR(100) NOT NULL,
  `id_teacher` INT NOT NULL,
  PRIMARY KEY (`subject_id`),
  UNIQUE INDEX `title_UNIQUE` (`title` ASC) VISIBLE,
  UNIQUE INDEX `subject_id_UNIQUE` (`subject_id` ASC) VISIBLE,
  UNIQUE INDEX `id_teacher_UNIQUE` (`id_teacher` ASC) VISIBLE)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`Students`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `mydb`.`Students` ;

CREATE TABLE IF NOT EXISTS `mydb`.`Students` (
  `telegram_user_id` INT NOT NULL,
  `username` VARCHAR(45) NULL,
  `firstname` VARCHAR(45) NULL,
  PRIMARY KEY (`telegram_user_id`),
  UNIQUE INDEX `telegram_user_id_UNIQUE` (`telegram_user_id` ASC) VISIBLE,
  UNIQUE INDEX `username_UNIQUE` (`username` ASC) VISIBLE)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`Queues`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `mydb`.`Queues` ;

CREATE TABLE IF NOT EXISTS `mydb`.`Queues` (
  `id_queue` INT NOT NULL AUTO_INCREMENT,
  `subject_id` INT NOT NULL,
  PRIMARY KEY (`id_queue`),
  UNIQUE INDEX `id_queue_UNIQUE` (`id_queue` ASC) VISIBLE,
  UNIQUE INDEX `subject_id_UNIQUE` (`subject_id` ASC) VISIBLE,
  CONSTRAINT `subject_id fk from Queue to Subjects`
    FOREIGN KEY (`subject_id`)
    REFERENCES `mydb`.`Subjects` (`subject_id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`Sign_ups`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `mydb`.`Sign_ups` ;

CREATE TABLE IF NOT EXISTS `mydb`.`Sign_ups` (
  `id_sign_up` INT NOT NULL AUTO_INCREMENT,
  `id_queue` INT NOT NULL,
  `telegram_user_id` INT NOT NULL,
  `position` INT NOT NULL,
  PRIMARY KEY (`id_sign_up`),
  UNIQUE INDEX `position_UNIQUE` (`position` ASC) VISIBLE,
  UNIQUE INDEX `id_queue_UNIQUE` (`id_queue` ASC) VISIBLE,
  UNIQUE INDEX `telegram_user_id_UNIQUE` (`telegram_user_id` ASC) VISIBLE,
  CONSTRAINT `id_queue fk from Sign_ups to Queue`
    FOREIGN KEY (`id_queue`)
    REFERENCES `mydb`.`Queues` (`id_queue`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `telegram_user_id fk from Sign_ups to Students`
    FOREIGN KEY (`telegram_user_id`)
    REFERENCES `mydb`.`Students` (`telegram_user_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`Teachers`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `mydb`.`Teachers` ;

CREATE TABLE IF NOT EXISTS `mydb`.`Teachers` (
  `id_teacher` INT NOT NULL AUTO_INCREMENT,
  `username_telegram` VARCHAR(45) NULL,
  `phone_number` CHAR(13) NULL,
  `email` VARCHAR(60) NULL,
  `info` TEXT(1000) NULL,
  PRIMARY KEY (`id_teacher`),
  UNIQUE INDEX `id_teacher_UNIQUE` (`id_teacher` ASC) VISIBLE,
  UNIQUE INDEX `phone_number_UNIQUE` (`phone_number` ASC) VISIBLE,
  UNIQUE INDEX `email_UNIQUE` (`email` ASC) VISIBLE,
  CONSTRAINT `id_teacher fk from Teachers to Subjects`
    FOREIGN KEY (`id_teacher`)
    REFERENCES `mydb`.`Subjects` (`id_teacher`)
    ON DELETE NO ACTION
    ON UPDATE CASCADE)
ENGINE = InnoDB;


SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;
